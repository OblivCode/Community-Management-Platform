import pytest
from src.auth import validate_user


class TestAuth:
    def test_validate_user(self, test_app, create_user):
        with test_app.app_context():
            # Create user
            test_username = "testuser"
            test_password = "testpassword"
            create_user(test_username, test_password, "user")
            
            # Validate the user exists and authenticates
            assert validate_user(test_username, test_password) is not None

    

    
