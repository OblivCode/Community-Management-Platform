import pytest
from src.models import Budget, Transaction, Document, User, db
from datetime import datetime


class TestRoutes:

    def test_login_page_loads(self, test_app):
        """Validate that the login page loads successfully."""
        with test_app.test_client() as client:
            response = client.get('/login')
            assert response.status_code == 200
            assert b"Login" in response.data

    def test_register_page_loads(self, test_app):
        """Validate that the register page loads successfully."""
        with test_app.test_client() as client:
            response = client.get('/register')
            assert response.status_code == 200

    def test_root_redirects_to_login(self, test_app):
        """Validate that the root URL redirects to login."""
        with test_app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 302
            assert "/login" in response.headers["Location"]

    def test_dashboard_redirects_if_unauthenticated(self, test_app):
        """Validate that dashboard redirects to login when not logged in."""
        with test_app.test_client() as client:
            response = client.get('/dashboard')
            assert response.status_code == 302
            assert "/login" in response.headers["Location"]

    def test_settings_redirects_if_unauthenticated(self, test_app):
        """Validate that settings page redirects to login when not logged in."""
        with test_app.test_client() as client:
            response = client.get('/settings')
            assert response.status_code == 302
            assert "/login" in response.headers["Location"]

    def test_events_redirects_if_unauthenticated(self, test_app):
        """Validate that events page redirects to login when not logged in."""
        with test_app.test_client() as client:
            response = client.get('/events')
            assert response.status_code == 302
            assert "/login" in response.headers["Location"]

    def test_assets_redirects_if_unauthenticated(self, test_app):
        """Validate that assets page redirects to login when not logged in."""
        with test_app.test_client() as client:
            response = client.get('/assets')
            assert response.status_code == 302
            assert "/login" in response.headers["Location"]

    def test_documents_redirects_if_unauthenticated(self, test_app):
        """Validate that documents page redirects to login when not logged in."""
        with test_app.test_client() as client:
            response = client.get('/documents')
            assert response.status_code == 302
            assert "/login" in response.headers["Location"]

    def test_expenses_redirects_if_unauthenticated(self, test_app):
        """Validate that expenses page redirects to login when not logged in."""
        with test_app.test_client() as client:
            response = client.get('/expenses')
            assert response.status_code == 302
            assert "/login" in response.headers["Location"]

    def test_dashboard_loads_if_authenticated(self, test_app, create_user):
        """Validate dashboard loads successfully when logged in."""
        with test_app.test_client() as client:
            # Create user and login
            username = "dashboard_user"
            password = "testpassword"
            with test_app.app_context():
                create_user(username, password, "user")

            # Login first
            client.post('/login', data={"username": username, "password": password})

            # Access dashboard
            response = client.get('/dashboard')
            assert response.status_code == 200
            assert b"Dashboard" in response.data

    def test_all_authenticated_pages_load(self, test_app, create_user):
        """Validate all main pages load when logged in."""
        with test_app.test_client() as client:
            username = "full_route_user"
            password = "testpassword"
            with test_app.app_context():
                create_user(username, password, "user")

            # Login
            client.post('/login', data={"username": username, "password": password})

            # Test each page loads correctly
            pages = [
                ('/dashboard', b'Dashboard'),
                ('/settings', b'Settings'),
                ('/events', b'Events'),
                ('/assets', b'Assets'),
                ('/documents', b'Documents'),
                ('/expenses', b'Expenses')
            ]

            for route, expected_text in pages:
                response = client.get(route)
                assert response.status_code == 200, f"Page {route} failed to load"
                assert expected_text in response.data, f"Page {route} missing expected content"

    def test_successful_login(self, test_app, create_user):
        """Validate that a user can successfully log in."""
        with test_app.test_client() as client:
            username = "login_success_user"
            password = "password123"
            with test_app.app_context():
                create_user(username, password, "user")

            # Login with correct credentials
            response = client.post('/login', data={"username": username, "password": password})
            assert response.status_code == 302  # Redirect after success

            # Follow redirect to dashboard
            response = client.get(response.headers["Location"])
            assert response.status_code == 200

    def test_failed_login_wrong_password(self, test_app, create_user):
        """Validate that login fails with wrong password."""
        with test_app.test_client() as client:
            username = "wrong_pass_user"
            password = "correctpassword"
            with test_app.app_context():
                create_user(username, password, "user")

            # Login with wrong password
            response = client.post('/login', data={"username": username, "password": "wrongpassword"})
            assert response.status_code == 200  # Stays on login page
            assert b"Invalid" in response.data or b"incorrect" in response.data.lower()

    def test_logout_clears_session(self, test_app, create_user):
        """Validate that logout clears the user session."""
        with test_app.test_client() as client:
            username = "logout_user"
            password = "password"
            with test_app.app_context():
                create_user(username, password, "user")

            # Login first
            client.post('/login', data={"username": username, "password": password})

            # Logout
            client.get('/logout')

            # Try to access protected page - should redirect
            response = client.get('/dashboard')
            assert response.status_code == 302

    def test_reimbursement_shows_no_receipt_notice(self, test_app, create_user):
        """Validate that transactions without receipts show a notice."""
        with test_app.test_client() as client:
            user = create_user("reimb_no_receipt_user", "password", "user")
            budget = Budget(year="2025", total_fund=1000.0, remaining_fund=500.0)
            db.session.add(budget)
            db.session.commit()

            # Create transaction without a document (no receipt)
            txn = Transaction(
                cost=10.0,
                currency="GBP",
                note="No receipt transaction",
                timestamp=datetime.now(),
                category="Misc",
                author=user.id,
                budget_id=budget.id
            )
            db.session.add(txn)
            db.session.commit()
            txn_id = txn.id

            # Login and view reimbursement
            client.post('/login', data={"username": "reimb_no_receipt_user", "password": "password"})
            response = client.get(f'/expenses/{txn_id}/reimbursement')

            assert response.status_code == 200
            assert b"[ NO RECEIPT ATTACHED ]" in response.data

    def test_reimbursement_shows_receipt_attached(self, test_app, create_user):
        """Validate that transactions with receipts show the receipt info."""
        with test_app.test_client() as client:
            user = create_user("reimb_yes_receipt_user", "password", "user")
            budget = Budget(year="2025", total_fund=1000.0, remaining_fund=500.0)
            db.session.add(budget)
            db.session.commit()

            # Create a document (receipt)
            doc = Document(
                note="Store receipt",
                filename="receipt.jpg",
                timestamp=datetime.now(),
                uploaded_by=user.id
            )
            db.session.add(doc)
            db.session.commit()

            # Create transaction with the receipt attached
            txn = Transaction(
                cost=25.0,
                currency="GBP",
                note="With receipt",
                timestamp=datetime.now(),
                category="Equipment",
                author=user.id,
                budget_id=budget.id,
                document_id=doc.id
            )
            db.session.add(txn)
            db.session.commit()
            txn_id = txn.id

            # Login and view reimbursement
            client.post('/login', data={"username": "reimb_yes_receipt_user", "password": "password"})
            response = client.get(f'/expenses/{txn_id}/reimbursement')

            assert response.status_code == 200
            assert b"receipt.jpg" in response.data or b"Receipt Attached" in response.data

    def test_reimbursement_nonexistent_transaction(self, test_app, create_user):
        """Validate that viewing a nonexistent transaction redirects."""
        with test_app.test_client() as client:
            create_user("reimb_bad_user", "password", "user")
            client.post('/login', data={"username": "reimb_bad_user", "password": "password"})

            # Try to view reimbursement for a transaction that doesn't exist
            # The route redirects because the transaction ID is invalid
            response = client.get('/expenses/99999/reimbursement')
            assert response.status_code == 302

    def test_annual_summary_valid_year(self, test_app, create_user):
        """Validate that annual summary shows correct data for a valid year."""
        with test_app.test_client() as client:
            create_user("summary_user", "password", "Admin")

            with test_app.app_context():
                user = User.query.filter_by(username="summary_user").first()
                budget = Budget(year="2030", total_fund=5000.0, remaining_fund=4500.0)
                db.session.add(budget)
                db.session.commit()

                # Create some transactions
                t1 = Transaction(
                    cost=100.0,
                    note="Tx1",
                    timestamp=datetime(2030, 1, 1),
                    category="Misc",
                    author=user.id,
                    budget_id=budget.id
                )
                t2 = Transaction(
                    cost=400.0,
                    note="Tx2",
                    timestamp=datetime(2030, 2, 1),
                    category="Equipment",
                    author=user.id,
                    budget_id=budget.id
                )
                db.session.add_all([t1, t2])
                db.session.commit()

            # Login and view summary
            client.post('/login', data={"username": "summary_user", "password": "password"})
            response = client.get('/expenses/2030/summary')

            assert response.status_code == 200
            assert b"2030" in response.data
            assert b"Annual Financial Ledger" in response.data
            assert b"Tx1" in response.data
            assert b"Tx2" in response.data

    def test_annual_summary_invalid_year_redirects(self, test_app, create_user):
        """Validate that invalid year redirects with a flash message."""
        with test_app.test_client() as client:
            create_user("summary_invalid_user", "password", "Admin")
            client.post('/login', data={"username": "summary_invalid_user", "password": "password"})

            # Try a year with no budget
            response = client.get('/expenses/2099/summary')
            assert response.status_code == 302  # Redirect

    def test_annual_summary_unauthenticated(self, test_app):
        """Validate that unauthenticated users cannot view annual summary."""
        with test_app.test_client() as client:
            response = client.get('/expenses/2025/summary')
            assert response.status_code == 302
            assert "/login" in response.headers["Location"]

    def test_register_new_user(self, test_app):
        """Validate that a new user can register successfully."""
        with test_app.test_client() as client:
            response = client.post('/register', data={
                "username": "new_register_user",
                "password": "newpassword123",
                "confirm_password": "newpassword123"
            })
            # Should redirect to login or dashboard after success
            assert response.status_code in [302, 200]

    def test_register_duplicate_username(self, test_app, create_user):
        """Validate that registering with existing username fails."""
        with test_app.test_client() as client:
            # Create existing user
            with test_app.app_context():
                create_user("existing_user", "password", "user")

            # Try to register with same username
            response = client.post('/register', data={
                "username": "existing_user",
                "password": "differentpassword",
                "confirm_password": "differentpassword"
            })
            # Should redirect since username already exists
            assert response.status_code == 302

    def test_expense_creation_requires_auth(self, test_app):
        """Validate that creating expense without login redirects."""
        with test_app.test_client() as client:
            response = client.post('/expenses', data={
                "cost": "50.00",
                "note": "Test expense"
            })
            assert response.status_code == 302

    def test_dashboard_shows_user_info(self, test_app, create_user):
        """Validate that dashboard shows the logged-in user's info."""
        with test_app.test_client() as client:
            username = "dashboard_info_user"
            with test_app.app_context():
                create_user(username, password="password", role="Admin")

            client.post('/login', data={"username": username, "password": "password"})
            response = client.get('/dashboard')

            assert response.status_code == 200
            assert username.encode() in response.data

    def test_settings_page_has_currency_options(self, test_app, create_user):
        """Validate that settings page has currency selection."""
        with test_app.test_client() as client:
            create_user("settings_currency_user", "password", "user")
            client.post('/login', data={"username": "settings_currency_user", "password": "password"})

            response = client.get('/settings')
            assert response.status_code == 200
            assert b"currency" in response.data.lower() or b"Currency" in response.data

    def test_events_page_shows_events_list(self, test_app, create_user):
        """Validate that events page displays events."""
        with test_app.test_client() as client:
            create_user("events_view_user", "password", "user")
            client.post('/login', data={"username": "events_view_user", "password": "password"})

            response = client.get('/events')
            assert response.status_code == 200
            assert b"Events" in response.data or b"event" in response.data.lower()

    def test_assets_page_shows_assets_list(self, test_app, create_user):
        """Validate that assets page displays assets."""
        with test_app.test_client() as client:
            create_user("assets_view_user", "password", "user")
            client.post('/login', data={"username": "assets_view_user", "password": "password"})

            response = client.get('/assets')
            assert response.status_code == 200
            assert b"Assets" in response.data or b"asset" in response.data.lower()

    # ============================
    # EDGE CASE TESTS
    # ============================

    def test_login_with_empty_credentials(self, test_app):
        """Validate that login fails with empty credentials."""
        with test_app.test_client() as client:
            response = client.post('/login', data={"username": "", "password": ""})
            assert response.status_code == 200  # Stays on page, shows error

    def test_large_transaction_amount(self, test_app, create_user):
        """Validate that large transaction amounts are handled correctly."""
        with test_app.test_client() as client:
            user = create_user("large_amount_user", "password", "user")
            budget = Budget(year="2035", total_fund=1000000.0, remaining_fund=1000000.0)
            db.session.add(budget)
            db.session.commit()

            txn = Transaction(
                cost=999999.99,
                currency="GBP",
                note="Large transaction",
                timestamp=datetime.now(),
                category="Equipment",
                author=user.id,
                budget_id=budget.id
            )
            db.session.add(txn)
            db.session.commit()

            client.post('/login', data={"username": "large_amount_user", "password": "password"})
            response = client.get('/expenses')

            assert response.status_code == 200

    def test_special_characters_in_note(self, test_app, create_user):
        """Validate that special characters in transaction notes are handled."""
        with test_app.test_client() as client:
            user = create_user("special_char_user", "password", "user")
            budget = Budget(year="2036", total_fund=1000.0, remaining_fund=1000.0)
            db.session.add(budget)
            db.session.commit()

            special_note = "Test <script>alert('xss')</script> & \"quotes\""
            txn = Transaction(
                cost=10.0,
                currency="GBP",
                note=special_note,
                timestamp=datetime.now(),
                category="Misc",
                author=user.id,
                budget_id=budget.id
            )
            db.session.add(txn)
            db.session.commit()

            client.post('/login', data={"username": "special_char_user", "password": "password"})
            response = client.get('/expenses')

            # Page should load without crashing
            assert response.status_code == 200