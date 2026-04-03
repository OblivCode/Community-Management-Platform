from flask import Blueprint, session, render_template, request, redirect, flash
import datetime
from ..auth import check_authentication, validate_user

auth_bp = Blueprint('auth', __name__)

# Login
@auth_bp.route('/login', methods=['GET'])
def login_get():
    if check_authentication():
        return redirect("/dashboard")
    return render_template('login.html')


@auth_bp.route('/login', methods=['POST'])
def login_post():
    username = request.form.get("username")
    password = request.form.get("password")

    valid = validate_user(username, password)

    if valid:
        session.clear() # Always clear the session on a fresh login
        session["user_id"] = valid.id
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
