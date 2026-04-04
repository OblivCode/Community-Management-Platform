import pytest

class TestRoutes:
    def test_login_page_loads(self, test_app):
        """Validate that the login page loads successfully (HTTP 200)."""
        with test_app.test_client() as client:
            response = client.get('/login')
            assert response.status_code == 200
            assert b"Login" in response.data

    def test_dashboard_redirects_if_unauthenticated(self, test_app):
        """Validate dashboard redirects to login if not authenticated (HTTP 302)."""
        with test_app.test_client() as client:
            response = client.get('/dashboard')
            assert response.status_code == 302
            assert "/login" in response.headers["Location"]

    def test_dashboard_loads_if_authenticated(self, test_app, create_user):
        """Validate dashboard loads successfully when logged in."""
        with test_app.test_client() as client:
            # Create user
            with test_app.app_context():
                username = "route_test_user"
                password = "testpassword"
                create_user(username, password, "user")

            # Login
            response = client.post('/login', data={"username": username, "password": password})
            assert response.status_code == 302 # Redirects to /dashboard

            # Get dashboard
            response = client.get('/dashboard')
            assert response.status_code == 200
            assert b"Dashboard" in response.data

    def test_all_authenticated_routes(self, test_app, create_user):
        """Validate all standard app pages load successfully when logged in."""
        with test_app.test_client() as client:
            with test_app.app_context():
                username = "full_route_test_user"
                password = "testpassword"
                create_user(username, password, "user")

            client.post('/login', data={"username": username, "password": password})

            routes = [
                ('/dashboard', b'Dashboard'),
                ('/settings', b'Settings'),
                ('/events', b'Events'),
                ('/assets', b'Assets'),
                ('/documents', b'Documents'),
                ('/expenses', b'Expenses')
            ]

            for route, expected_text in routes:
                response = client.get(route)
                assert response.status_code == 200, f"Route {route} failed with status {response.status_code}"
                assert expected_text in response.data, f"Route {route} missing expected text {expected_text}"

    def test_reimbursement_route(self, test_app, create_user):
        """Validate the reimbursement route correctly displays and handles receipt conditions."""
        from src.models import Budget, Transaction, Document, db
        from datetime import datetime
        with test_app.test_client() as client:
            with test_app.app_context():
                user = create_user("reimb_user", "password", "user")
                budget = Budget(year="2025", total_fund=1000.0, remaining_fund=500.0)
                
                # Transaction without receipt
                t_no_receipt = Transaction(cost=10.0, currency="GBP", note="No receipt", 
                                           timestamp=datetime.now(), category="Misc", author=user.id, budget_id=1)
                                           
                # Transaction with receipt 
                doc = Document(note="A receipt", filename="receipt.jpg", timestamp=datetime.now(), uploaded_by=user.id)
                db.session.add(budget)
                db.session.add(t_no_receipt)
                db.session.add(doc)
                db.session.commit()
                
                t_receipt = Transaction(cost=20.0, currency="GBP", note="With receipt", 
                                        timestamp=datetime.now(), category="Misc", author=user.id, budget_id=budget.id,
                                        document_id=doc.id)
                db.session.add(t_receipt)
                db.session.commit()
                
                id_no = t_no_receipt.id
                id_yes = t_receipt.id

            client.post('/login', data={"username": "reimb_user", "password": "password"})
            
            # Test transaction without receipt
            response1 = client.get(f'/expenses/{id_no}/reimbursement')
            assert response1.status_code == 200
            assert b"[ NO RECEIPT ATTACHED ]" in response1.data
            
            # Test transaction with receipt
            response2 = client.get(f'/expenses/{id_yes}/reimbursement')
            assert response2.status_code == 200
            assert b"receipt.jpg" in response2.data or b"Receipt Attached" in response2.data

    def test_annual_summary_route(self, test_app, create_user):
        from src.models import Budget, Transaction, User, db
        import datetime
        
        with test_app.test_client() as client:
            # Create user (uses the fixture to properly hash password)
            create_user("summary_user", "password", "Admin")
            
            with test_app.app_context():
                user = User.query.filter_by(username="summary_user").first()
                # Setup budget and transactions
                budget = Budget(year="2030", total_fund=5000.0, remaining_fund=4500.0)
                db.session.add(budget)
                db.session.commit()
                
                t1 = Transaction(cost=100.0, note="Tx1", timestamp=datetime.datetime(2030, 1, 1), category="Misc", author=user.id, budget_id=budget.id)
                t2 = Transaction(cost=400.0, note="Tx2", timestamp=datetime.datetime(2030, 2, 1), category="Equipment", author=user.id, budget_id=budget.id)
                db.session.add_all([t1, t2])
                db.session.commit()
                
            client.post('/login', data={"username": "summary_user", "password": "password"})
            
            # Check invalid year
            response_invalid = client.get('/expenses/2099/summary')
            assert response_invalid.status_code == 302 # Redirect due to flash
            
            # Check valid year
            response_valid = client.get('/expenses/2030/summary')
            assert response_valid.status_code == 200
            assert b"2030" in response_valid.data
            assert b"Annual Financial Ledger" in response_valid.data
            assert b"Tx1" in response_valid.data
            assert b"Tx2" in response_valid.data
