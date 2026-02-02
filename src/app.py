from flask import Flask, render_template, request, session, redirect, flash
from auth import validateUser
from models import AssetStatus, Document, Transaction, db, User, Budget, Asset
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
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/dashboard')
def dashboard():
    if not session.get("username"):
        return redirect("/login")
    # 1. Build Dashboard
    # A. Budget/Expense Overview
    budget = Budget.query.first()
    total_budget = budget.total_fund
    remaining_budget = budget.remaining_fund 
    budget_year = budget.year
    count_no_receipt = Transaction.query.filter_by(budget_id=budget.id, document_id=None).count()
    # B. Asset Overview
    count_assets = Asset.query.count()
    count_assets_damaged = Asset.query.filter(Asset.status == AssetStatus.DAMAGED.value).count()
    # C. Document Overview
    count_documents = Document.query.count()
    unlinked_documents = Document.query.filter_by(parent_id=None).count()
    # D. Action log
    # Retrieve last 3 transactions
    recent_transactions = Transaction.query.order_by(Transaction.timestamp.desc()).filter_by(budget_id=budget.id).limit(3).all()
    # Temporary variables
    minimum_budget_health = total_budget * 0.2
    currency = '£'
    return render_template('dashboard.html', username = session["username"],  currency=currency, budget_year = budget_year, minimum_budget_health = minimum_budget_health, total_budget=total_budget, remaining_budget=remaining_budget, count_no_receipt=count_no_receipt, count_assets=count_assets, count_assets_damaged=count_assets_damaged, count_documents=count_documents, unlinked_documents=unlinked_documents, recent_transactions=recent_transactions)


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
