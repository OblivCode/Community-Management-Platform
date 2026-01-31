from flask import Flask, render_template, request, session, redirect, flash
from auth import validateUser

app = Flask(__name__)

# Configure session to expire on browser close
app.config["SESSION_PERMANENT"] = False 
app.secret_key = 'secret'

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():  
    if request.method == "POST":
        # Check if session exists, else get from form
        if session.get("username"):
            username = session["username"]
            password = session["password"]
        else:
            username = request.form.get("username")
            password = request.form.get("password")
        
        valid = validateUser(username, password)

        if valid:
            session["username"] = username
            session["password"] = password
            return redirect("/dashboard")
        else:
            flash("Invalid username or password", "error")
            return render_template('login.html')
    elif request.method == "GET":
        return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get("username"):
        return redirect("/login")
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run()