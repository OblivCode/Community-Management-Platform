import pytest
from datetime import datetime
from src.models import User, Budget, Asset, Transaction, Document, Setting, AssetStatus, Event, db


class TestDatabase:
    # ============================
    # BASIC TESTS: User Model
    # ============================

    def test_user_create(self, test_app):
        """Validate that a user is created with correct default values."""
        with test_app.app_context():
            # Create a basic user
            user = User(username="basic_user", password="password123", role="user")
            db.session.add(user)
            db.session.commit()

            # Check user exists and has expected default values
            assert user.id is not None
            assert user.username == "basic_user"
            assert user.password == "password123"
            assert user.role == "user"
            assert user.theme == "light"  # Default theme should be light

    def test_user_custom_theme(self, test_app):
        """Validate that a user can have a custom theme."""
        with test_app.app_context():
            # Create user with dark theme preference
            user = User(username="dark_user", password="password", role="user", theme="dark")
            db.session.add(user)
            db.session.commit()

            # Verify the theme was saved
            assert user.theme == "dark"

    # ============================
    # BASIC TESTS: Budget Model
    # ============================

    def test_budget_create(self, test_app):
        """Validate that a budget is created with correct default values."""
        with test_app.app_context():
            # Create a basic budget
            budget = Budget(year="2025", total_fund=1500.0, remaining_fund=1500.0)
            db.session.add(budget)
            db.session.commit()

            # Check budget exists with defaults
            assert budget.id is not None
            assert budget.year == "2025"
            assert budget.total_fund == 1500.0
            assert budget.remaining_fund == 1500.0
            assert budget.currency == "GBP"  # Default currency

    def test_budget_custom_currency(self, test_app):
        """Validate that a budget can have a custom currency."""
        with test_app.app_context():
            # Create budget with USD currency
            budget = Budget(year="2025", total_fund=2000.0, remaining_fund=2000.0, currency="USD")
            db.session.add(budget)
            db.session.commit()

            # Verify custom currency is saved
            assert budget.currency == "USD"

    # ============================
    # BASIC TESTS: Asset Model
    # ============================

    def test_asset_create(self, test_app):
        """Validate that an asset is created with correct default values."""
        with test_app.app_context():
            # Create a basic asset
            asset = Asset(name="Tent", count=5)
            db.session.add(asset)
            db.session.commit()

            # Check asset exists with defaults
            assert asset.id is not None
            assert asset.name == "Tent"
            assert asset.count == 5
            assert asset.status == AssetStatus.FINE  # Default status
            assert asset.location == "Storage"  # Default location

    def test_asset_custom_status_and_location(self, test_app):
        """Validate that an asset can have custom status and location."""
        with test_app.app_context():
            # Create asset with non-default values
            asset = Asset(name="Damaged Tent", count=1, status=AssetStatus.DAMAGED, location="Repair Shop")
            db.session.add(asset)
            db.session.commit()

            # Verify custom values are saved
            assert asset.status == AssetStatus.DAMAGED
            assert asset.location == "Repair Shop"

    # ============================
    # BASIC TESTS: Transaction Model
    # ============================

    def test_transaction_create(self, test_app, create_user):
        """Validate that a transaction is created with correct values."""
        with test_app.app_context():
            # Create user and budget first (needed for foreign keys)
            user = create_user("txn_user", "password", "user")
            budget = Budget(year="2025", total_fund=1000.0, remaining_fund=900.0)
            db.session.add(budget)
            db.session.commit()

            # Create a transaction linked to user and budget
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

            # Verify transaction was created and relationships work
            assert txn.id is not None
            assert txn.cost == 100.0
            assert txn.note == "Test expense"
            assert txn.user.username == "txn_user"
            assert txn.budget.year == "2025"

    # ============================
    # BASIC TESTS: Document Model
    # ============================

    def test_document_create(self, test_app, create_user):
        """Validate that a document is created with correct values."""
        with test_app.app_context():
            # Create user first (needed for foreign key)
            user = create_user("doc_user", "password", "user")

            # Create a document uploaded by this user
            doc = Document(
                note="Test document",
                filename="test.pdf",
                timestamp=datetime.now(),
                uploaded_by=user.id
            )
            db.session.add(doc)
            db.session.commit()

            # Verify document was created
            assert doc.id is not None
            assert doc.note == "Test document"
            assert doc.filename == "test.pdf"
            assert doc.uploader.username == "doc_user"

    # ============================
    # BASIC TESTS: Setting Model
    # ============================

    def test_setting_create(self, test_app):
        """Validate that a setting is created with correct values."""
        with test_app.app_context():
            # Create a basic setting
            setting = Setting(key="currency_code", value="GBP")
            db.session.add(setting)
            db.session.commit()

            # Verify setting was created
            assert setting.id is not None
            assert setting.key == "currency_code"
            assert setting.value == "GBP"

    # ============================
    # BASIC TESTS: Event Model
    # ============================

    def test_event_create(self, test_app):
        """Validate that an event is created with correct values."""
        with test_app.app_context():
            # Create an event with all required fields
            event = Event(
                title="Test Event",
                description="This is a test event",
                date=datetime.now()
            )
            db.session.add(event)
            db.session.commit()

            # Verify event was created
            assert event.id is not None
            assert event.title == "Test Event"
            assert event.description == "This is a test event"

    # ============================
    # ADVANCED TESTS: Constraints and Edge Cases
    # ============================

    def test_user_unique_username(self, test_app, create_user):
        """Validate that duplicate usernames are not allowed."""
        with test_app.app_context():
            # Create first user with a unique username
            create_user("unique_user", "password", "user")

            # Try to create another user with the same username
            duplicate_user = User(username="unique_user", password="different", role="user")
            db.session.add(duplicate_user)

            # Verify this raises an error
            with pytest.raises(Exception):
                db.session.commit()

    def test_setting_unique_key(self, test_app):
        """Validate that duplicate setting keys are not allowed."""
        with test_app.app_context():
            # Create first setting with a unique key
            setting1 = Setting(key="unique_key", value="value1")
            db.session.add(setting1)
            db.session.commit()

            # Try to create another setting with the same key
            setting2 = Setting(key="unique_key", value="value2")
            db.session.add(setting2)

            # Verify this raises an error
            with pytest.raises(Exception):
                db.session.commit()

    def test_event_requires_title(self, test_app):
        """Validate that an event without a title fails to save."""
        with test_app.app_context():
            # Try to create an event missing the required title field
            event = Event(description="No title event", date=datetime.now())
            db.session.add(event)

            # Verify this raises an error (title should be required)
            with pytest.raises(Exception):
                db.session.commit()

    def test_transaction_links_to_user(self, test_app, create_user):
        """Validate that a transaction correctly links to its author."""
        with test_app.app_context():
            # Create user and budget
            user = create_user("link_test_user", "password", "user")
            budget = Budget(year="2026", total_fund=500.0, remaining_fund=500.0)
            db.session.add(budget)
            db.session.commit()

            # Create transaction
            txn = Transaction(
                cost=50.0,
                currency="GBP",
                note="Linked transaction",
                timestamp=datetime.now(),
                category="Misc",
                author=user.id,
                budget_id=budget.id
            )
            db.session.add(txn)
            db.session.commit()

            # Verify the transaction's user relationship works
            assert txn.user.id == user.id
            assert txn.user.username == "link_test_user"

    def test_transaction_links_to_budget(self, test_app, create_user):
        """Validate that a transaction correctly links to its budget."""
        with test_app.app_context():
            user = create_user("budget_link_user", "password", "user")
            budget = Budget(year="2027", total_fund=1000.0, remaining_fund=750.0)
            db.session.add(budget)
            db.session.commit()

            # Create transaction linked to the budget
            txn = Transaction(
                cost=250.0,
                currency="GBP",
                note="Budget link test",
                timestamp=datetime.now(),
                category="Equipment",
                author=user.id,
                budget_id=budget.id
            )
            db.session.add(txn)
            db.session.commit()

            # Verify transaction's budget relationship works
            assert txn.budget.id == budget.id
            assert txn.budget.year == "2027"
            assert txn.budget.remaining_fund == 750.0

    def test_asset_status_enum_values(self, test_app):
        """Validate that asset status can be set to different enum values."""
        with test_app.app_context():
            # Test DAMAGED status
            damaged = Asset(name="Damaged Item", count=1, status=AssetStatus.DAMAGED)
            db.session.add(damaged)
            db.session.commit()
            assert damaged.status == AssetStatus.DAMAGED

            # Test LOST status
            lost = Asset(name="Lost Item", count=1, status=AssetStatus.LOST)
            db.session.add(lost)
            db.session.commit()
            assert lost.status == AssetStatus.LOST

            # Note: UNDER_REPAIR is not a valid status in our model



    def test_multiple_transactions_per_budget(self, test_app, create_user):
        """Validate that a budget can have multiple transactions."""
        with test_app.app_context():
            user = create_user("multi_txn_user", "password", "user")
            budget = Budget(year="2029", total_fund=5000.0, remaining_fund=5000.0)
            db.session.add(budget)
            db.session.commit()

            # Create multiple transactions for the same budget
            txn1 = Transaction(cost=100.0, currency="GBP", note="First txn",
                             timestamp=datetime.now(), category="Misc",
                             author=user.id, budget_id=budget.id)
            txn2 = Transaction(cost=200.0, currency="GBP", note="Second txn",
                             timestamp=datetime.now(), category="Equipment",
                             author=user.id, budget_id=budget.id)
            txn3 = Transaction(cost=300.0, currency="GBP", note="Third txn",
                             timestamp=datetime.now(), category="Travel",
                             author=user.id, budget_id=budget.id)

            db.session.add_all([txn1, txn2, txn3])
            db.session.commit()

            # Verify all three transactions exist and link to the same budget
            assert txn1.id is not None
            assert txn2.id is not None
            assert txn3.id is not None
            assert txn1.budget_id == budget.id
            assert txn2.budget_id == budget.id
            assert txn3.budget_id == budget.id

    def test_document_uploader_relationship(self, test_app, create_user):
        """Validate that document correctly links to uploader."""
        with test_app.app_context():
            user = create_user("uploader_test", "password", "user")

            doc = Document(
                note="Receipt",
                filename="receipt.pdf",
                timestamp=datetime.now(),
                uploaded_by=user.id
            )
            db.session.add(doc)
            db.session.commit()

            # Verify document uploader relationship
            assert doc.uploader.id == user.id
            assert doc.uploader.username == "uploader_test"

    def test_user_role_assignment(self, test_app):
        """Validate that user role can be set to different roles."""
        with test_app.app_context():
            # Test Admin role
            admin = User(username="admin_user", password="password", role="Admin")
            db.session.add(admin)
            db.session.commit()
            assert admin.role == "Admin"

            # Test User role
            regular = User(username="regular_user", password="password", role="user")
            db.session.add(regular)
            db.session.commit()
            assert regular.role == "user"

    def test_asset_count_can_be_zero(self, test_app):
        """Validate that an asset can have zero count."""
        with test_app.app_context():
            asset = Asset(name="Empty Storage", count=0)
            db.session.add(asset)
            db.session.commit()

            assert asset.count == 0

    def test_setting_value_can_be_updated(self, test_app):
        """Validate that a setting's value can be updated after creation."""
        with test_app.app_context():
            # Create a setting
            setting = Setting(key="theme", value="light")
            db.session.add(setting)
            db.session.commit()

            # Update the value
            setting.value = "dark"
            db.session.commit()

            # Verify the value was updated
            updated = Setting.query.filter_by(key="theme").first()
            assert updated.value == "dark"

    def test_transaction_note_can_be_empty(self, test_app, create_user):
        """Validate that a transaction can have an empty note."""
        with test_app.app_context():
            user = create_user("empty_note_user", "password", "user")
            budget = Budget(year="2030", total_fund=1000.0, remaining_fund=1000.0)
            db.session.add(budget)
            db.session.commit()

            # Create transaction with empty note
            txn = Transaction(
                cost=50.0,
                currency="GBP",
                note="",
                timestamp=datetime.now(),
                category="Misc",
                author=user.id,
                budget_id=budget.id
            )
            db.session.add(txn)
            db.session.commit()

            assert txn.note == ""

    def test_budget_remaining_fund_can_be_zero(self, test_app):
        """Validate that a budget can have zero remaining funds."""
        with test_app.app_context():
            budget = Budget(year="2031", total_fund=1000.0, remaining_fund=0.0)
            db.session.add(budget)
            db.session.commit()

            assert budget.remaining_fund == 0.0

    def test_event_date_persistence(self, test_app):
        """Validate that event date is correctly saved and retrieved."""
        with test_app.app_context():
            event_date = datetime(2025, 6, 15, 10, 30, 0)
            event = Event(title="Dated Event", description="Test", date=event_date)
            db.session.add(event)
            db.session.commit()

            # Verify date was saved correctly
            retrieved = Event.query.filter_by(title="Dated Event").first()
            assert retrieved.date.year == 2025
            assert retrieved.date.month == 6
            assert retrieved.date.day == 15