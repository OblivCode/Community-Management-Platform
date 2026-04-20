import pytest
from werkzeug.security import generate_password_hash
from src.app import db, create_app
from src.models import User

# Fixture to create a user quickly in tests
# Helps avoid repeating user creation code across tests
@pytest.fixture
def create_user():
    def _create_user(username, password, role):
        user = User(username=username, password=generate_password_hash(password), role=role)
        db.session.add(user)
        db.session.commit()
        return user
    return _create_user

# Creates a fresh app instance for each test
# Uses a temporary in-memory database so tests dont affect real data
@pytest.fixture
def test_app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", 
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()