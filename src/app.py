from flask import Flask, render_template, request, session, redirect, flash
from auth import validateUser
from models import db, User, Budget
import os

app = Flask(__name__)

# Configure session to expire on browser close
app.config["SESSION_PERMANENT"] = False 
app.secret_key = 'secret'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cmp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


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
    
@app.route('/signout')
def signout():
    session.clear()
    return redirect('/login')

@app.route('/dashboard')
def dashboard():
    if not session.get("username"):
        return redirect("/login")
    return render_template('dashboard.html')


def setup_database():
    with app.app_context():
        # 1. Create all tables defined in models.py
        db.create_all()
        
        # 2. Check if we need to seed a Test User
        if not User.query.filter_by(username='Jay').first():
            print("⚡ Creating Test Data...")
            
            # Create Users
            jay = User(username='Jay', password='password123', role='Treasurer')
            skipper = User(username='Skipper', password='123', role='Captain')
            
            # Create a Budget for 2025
            budget = Budget(year='2025', total_fund=1500.0, remaining_fund=1500.0)
            
            # Add to Staging Area
            db.session.add(jay)
            db.session.add(skipper)
            db.session.add(budget)
            
            # Commit to Database
            db.session.commit()
            print("✅ Database initialized with Users: Jay (Treasurer) & Skipper (Captain)")



if __name__ == '__main__':
    app.run()
