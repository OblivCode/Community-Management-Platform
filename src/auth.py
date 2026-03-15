from .models import User
from flask import session

def validate_user(username, password):
    print(f"Validating user: {username}")
    # 1. Search for the user by username
    user = User.query.filter_by(username=username).first()

    # 2. If user exists AND password matches
    if user and user.password == password:
        return user
    # 3. Otherwise, return None
    return None

def check_authentication():
    if not session.get("username"):
        return False

    user = User.query.filter_by(username=session["username"]).first()
    if not user or user.password != session.get("password"):
        return False
    
    return True
