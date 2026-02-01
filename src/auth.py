from models import User

def validateUser(username, password):
    print(f"Validating user: {username}")
    # 1. Search for the user by username
    user = User.query.filter_by(username=username).first()

    # 2. If user exists AND password matches
    if user and user.password == password:
        return user
    # 3. Otherwise, return None
    return None