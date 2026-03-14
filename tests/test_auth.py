import pytest
from src.app import app, db
from src.models import User
from src.auth import validateUser


test_username = "testuser"
test_password = "testpassword"

@pytest.fixture
def test_app():
    print("Setting up auth test.")

    with app.app_context():
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
            from src.auth import validateUser
            assert validateUser(test_username, test_password) is not None

    

    
