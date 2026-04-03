from .models import User
from flask import session
from werkzeug.security import check_password_hash


def validate_user(username, password):
    user = User.query.filter_by(username=username).first()
    # Check the hashed password against what they typed
    if user and check_password_hash(user.password, password):
        return user
    return None


def check_authentication():
    # Only check for user_id now
    if not session.get("user_id"):
        return False

    user = User.query.get(session.get("user_id"))
    if not user:
        return False

    return True