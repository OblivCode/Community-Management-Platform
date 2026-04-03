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

