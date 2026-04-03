from flask import Blueprint, session, render_template, request, redirect, flash
import datetime
from werkzeug.security import generate_password_hash
from ..auth import check_authentication, validate_user
from ..models import User, db

auth_bp = Blueprint('auth', __name__)

# Login
@auth_bp.route('/login', methods=['GET'])
def login_get():
    if check_authentication():
        return redirect("/dashboard")
    return render_template('login.html')


@auth_bp.route('/login', methods=['POST'])
def login_post():
    # We don't need to pull from session anymore for a login attempt
    username = request.form.get("username")
    password = request.form.get("password")
        
    valid = validate_user(username, password)

    if valid:
        session.clear() # Always clear the session on a fresh login
        session["user_id"] = valid.id
        session["username"] = valid.username
        session["budget_year"] = str(datetime.datetime.now().year)
        return redirect("/dashboard")
    else:
        flash("Invalid username or password", "error")
        return render_template('login.html')

# Logout

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect('/login')

# Register
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        if check_authentication():
            return redirect("/dashboard")
        return render_template('register.html')
    
    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role") or "Member"
    
    if not username or not password:
        flash("Username and password are required.", "error")
        return redirect("/register")
        
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash("Username already exists.", "error")
        return redirect("/register")
        
    new_user = User(
        username=username,
        password=generate_password_hash(password),
        role=role
    )
    db.session.add(new_user)
    db.session.commit()
    
    flash("Registration successful. Please log in.", "success")
    return redirect("/login")
