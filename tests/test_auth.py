import pytest
from src.auth import validate_user
from src.models import User, db



class TestAuth:
    def test_user_correct_credentials(self, test_app, create_user):
        """Validate that the correct username and password works."""
        with test_app.app_context():
            # Create user
            username = "testuser"
            password = "testpassword"
            role = "user"
            create_user(username, password, role)

            # Validate the user exists and authenticates
            assert validate_user(username, password) is not None

    def test_user_wrong_credentials(self, test_app, create_user):
        """Validate the wrong username and password fails."""
        with test_app.app_context():
            # Create user
            username = "testuser_wrong"
            password = "testpassword_wrong"
            role = "user"
            create_user(username, password, role)

            # Validate the user does not authenticate
            assert validate_user("wronguser", "wrongpassword") is None

    def test_user_nonexist(self, test_app, create_user):
        """Validate that a non-existent user fails."""
        with test_app.app_context():
            # Create user
            username = "testuser_nonexist"
            password = "testpassword_nonexist"
            role = "user"

            # Validate the user does not authenticate
            assert validate_user(password, password) is None

    def test_user_deleted(self, test_app, create_user):
        """Validate that a deleted user fails."""
        with test_app.app_context():
            # Create user
            username = "testuser_deleted"
            password = "testpassword_deleted"
            role = "user"
            create_user(username, password, role)

            # Delete the user
            user = User.query.filter_by(username=username).first()
            db.session.delete(user)
            db.session.commit()

            # Validate the user does not authenticate
            assert validate_user(username, password) is None
    

    
