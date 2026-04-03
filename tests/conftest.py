import pytest
from werkzeug.security import generate_password_hash
from src.app import db, create_app
from src.models import User

@pytest.fixture
def create_user():
    def _create_user(username, password, role):
        user = User(username=username, password=generate_password_hash(password), role=role)
        db.session.add(user)
        db.session.commit()
        return user
    return _create_user

@pytest.fixture
def test_app():
    """Create and configure app instance for each test."""

    print("Setting up app instance test.")
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", 
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    })

    with app.app_context():
        db.create_all()

        yield app

        print("Tests done. Cleaning up.")
        db.session.remove()
        db.drop_all()

