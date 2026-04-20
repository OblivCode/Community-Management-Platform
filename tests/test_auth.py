import pytest
from src.auth import validate_user
from src.models import User, db


class TestAuth:
    # --- Basic Tests: Authentication Logic ---

    def test_user_correct_credentials(self, test_app, create_user):
        """Validate that the correct username and password works."""
        with test_app.app_context():
            # Create a user with known credentials
            username = "testuser"
            password = "testpassword"
            role = "user"
            create_user(username, password, role)

            # Validate the user can authenticate with correct details
            assert validate_user(username, password) is not None

    def test_user_wrong_credentials(self, test_app, create_user):
        """Validate the wrong username and password fails."""
        with test_app.app_context():
            # Create a user with known credentials
            username = "testuser_wrong"
            password = "testpassword_wrong"
            role = "user"
            create_user(username, password, role)

            # Validate authentication fails with wrong details
            assert validate_user("wronguser", "wrongpassword") is None

    def test_user_nonexistent(self, test_app):
        """Validate that a user who does not exist cannot authenticate."""
        with test_app.app_context():
            # Try to authenticate a user that was never created
            # This should fail and return None
            assert validate_user("ghost_user", "anypassword") is None

    def test_user_deleted(self, test_app, create_user):
        """Validate that a deleted user cannot authenticate."""
        with test_app.app_context():
            # Create a user then delete them
            username = "testuser_deleted"
            password = "testpassword_deleted"
            role = "user"
            create_user(username, password, role)

            # Remove the user from the database
            user = User.query.filter_by(username=username).first()
            db.session.delete(user)
            db.session.commit()

            # Validate deleted user cannot authenticate
            assert validate_user(username, password) is None

    def test_user_wrong_password(self, test_app, create_user):
        """Validate that a user cannot login with a wrong password."""
        with test_app.app_context():
            # Create a user with a known password
            username = "testuser_wrongpass"
            password = "correctpassword"
            create_user(username, password, "user")

            # Try to login with the wrong password
            assert validate_user(username, "wrongpassword") is None
