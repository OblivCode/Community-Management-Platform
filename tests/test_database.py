import pytest
from datetime import datetime
from src.models import User, Budget, Asset, Transaction, Document, Setting, AssetStatus, db


class TestDatabase:
    # User
    def test_user_create(self, test_app):
        """Validate that a user is created."""
        with test_app.app_context():
            # Create user
            username = "testuser_create"
            password = "testpassword"
            role = "user"
            user = User(username=username, password=password, role=role)
            db.session.add(user)
            db.session.commit()

            # Validate the user was created with correct fields
            assert user.id is not None
            assert user.username == username
            assert user.password == password
            assert user.role == role
            assert user.theme == "light"  # Default value

    def test_user_custom_theme(self, test_app):
        """Validate that a user's theme choice saves."""
        with test_app.app_context():
            # Create user with a dark theme
            user = User(username="darkmode_user", password="password", role="user", theme="dark")
            db.session.add(user)
            db.session.commit()

            # Validate the theme is saved
            assert user.theme == "dark"

    def test_user_unique_username(self, test_app, create_user):
        """Validate that duplicate usernames are not allowed."""
        with test_app.app_context():
            # Create first user
            username = "duplicate_user"
            password = "testpassword"
            role = "user"
            create_user(username, password, role)

            # Create second user with same username
            with pytest.raises(Exception):  
                create_user(username, "different", role)
    # Budget year
    def test_budget_create(self, test_app):
        """Validate that a budget is created."""
        with test_app.app_context():
            # Create budget
            year = "2025"
            total_fund = 1500.0
            remaining_fund = 1500.0
            budget = Budget(year=year, total_fund=total_fund, remaining_fund=remaining_fund)
            db.session.add(budget)
            db.session.commit()

            # Validate the budget was created with correct defaults
            assert budget.id is not None
            assert budget.year == year
            assert budget.total_fund == total_fund
            assert budget.remaining_fund == remaining_fund
            assert budget.currency == "GBP"  

    def test_budget_custom_currency(self, test_app):
        """Validate that a budget can have a custom currency."""
        with test_app.app_context():
            # Create budget with custom currency
            budget = Budget(year="2025", total_fund=1500.0, remaining_fund=1500.0, currency="USD")
            db.session.add(budget)
            db.session.commit()

            # Validate the new currency is saved
            assert budget.currency == "USD"

    # Assets
    def test_asset_create(self, test_app):
        """Validate that an asset is created."""
        with test_app.app_context():
            # Create asset
            name = "Tent"
            count = 5
            asset = Asset(name=name, count=count)
            db.session.add(asset)
            db.session.commit()

            # Validate the asset was created with correct defaults
            assert asset.id is not None
            assert asset.name == name
            assert asset.count == count
            assert asset.status == AssetStatus.FINE  
            assert asset.location == "Storage"  

    def test_asset_custom_status_and_location(self, test_app):
        """Validate that an asset can have custom status and location."""
        with test_app.app_context():
            # Create asset with custom status and location
            asset = Asset(name="Damaged Tent", count=1, status=AssetStatus.DAMAGED, location="Repair Shop")
            db.session.add(asset)
            db.session.commit()

            # Validate the new values are saved
            assert asset.status == AssetStatus.DAMAGED
            assert asset.location == "Repair Shop"

    # Transactions

    # Transactions
    def test_transaction_create(self, test_app, create_user):
        """Validate that a transaction is created."""
        with test_app.app_context():
            # Create user and budget first for foreign keys
            user = create_user("txn_user", "password", "user")
            budget = Budget(year="2025", total_fund=1000.0, remaining_fund=900.0)
            db.session.add(budget)
            db.session.commit()

            # Create transaction
            txn = Transaction(
                cost=100.0,
                currency="GBP",
                note="Test expense",
                timestamp=datetime.now(),
                category="Equipment",
                author=user.id,
                budget_id=budget.id
            )
            db.session.add(txn)
            db.session.commit()

            # Validate the transaction was created
            assert txn.id is not None
            assert txn.cost == 100.0
            assert txn.note == "Test expense"
            assert txn.user.username == "txn_user"
            assert txn.budget.year == "2025"

    # Documents
    def test_document_create(self, test_app, create_user):
        """Validate that a document is created."""
        with test_app.app_context():
            # Create user first for foreign key
            user = create_user("doc_user", "password", "user")

            # Create document
            doc = Document(
                note="Test document",
                filename="test.pdf",
                timestamp=datetime.now(),
                uploaded_by=user.id
            )
            db.session.add(doc)
            db.session.commit()

            # Validate the document was created
            assert doc.id is not None
            assert doc.note == "Test document"
            assert doc.filename == "test.pdf"
            assert doc.uploader.username == "doc_user"

    # Settings
    def test_setting_create(self, test_app):
        """Validate that a setting is created."""
        with test_app.app_context():
            # Create setting
            setting = Setting(key="currency_code", value="GBP")
            db.session.add(setting)
            db.session.commit()

            # Validate the setting was created
            assert setting.id is not None
            assert setting.key == "currency_code"
            assert setting.value == "GBP"

    def test_setting_unique_key(self, test_app):
        """Validate that duplicate setting keys are not allowed."""
        with test_app.app_context():
            # Create first setting
            setting1 = Setting(key="unique_key", value="value1")
            db.session.add(setting1)
            db.session.commit()

            # Create second setting with same key
            setting2 = Setting(key="unique_key", value="value2")
            db.session.add(setting2)
            
            # Validate that commit raises an error
            with pytest.raises(Exception):
                db.session.commit()
