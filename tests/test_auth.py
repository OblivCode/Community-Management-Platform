import pytest
from src.app import app, db, configure_db
from src.models import User
from src.auth import validate_user


test_username = "testuser"
test_password = "testpassword"

@pytest.fixture
def test_app():
    print("Setting up auth test.")

    with app.app_context():
        configure_db()
        db.create_all()

        # Test user
        user = User(username=test_username, password=test_password, role="Captain")
        db.session.add(user)
        db.session.commit()

        yield app

        print("Tests done. Cleaning up.")
        db.session.remove()
        db.drop_all()

class TestAuth:
    def test_validateUser(self, test_app):
        with app.app_context():
            from src.auth import validate_user
            assert validate_user(test_username, test_password) is not None

    

    
