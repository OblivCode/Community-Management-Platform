from flask import Flask, jsonify, render_template, request, session, redirect, flash
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

# Dashboard Route
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
    
    # TODO: Handle flashing messages for various actions across the app
    # TODO: Develop recent activity log for actions like asset updates, document uploads, etc.
    # Temporary variables
    # TODO: implement settings and map currency symbol and budget health threshold
    minimum_budget_health = total_budget * 0.2
    currency = '£'
    
    return render_template('dashboard.html', username = session["username"],  currency=currency, budget_year = budget_year, minimum_budget_health = minimum_budget_health, total_budget=total_budget, remaining_budget=remaining_budget, count_no_receipt=count_no_receipt, count_assets=count_assets, count_assets_damaged=count_assets_damaged, count_documents=count_documents, unlinked_documents=unlinked_documents, recent_transactions=recent_transactions)

# Asset Management Route

@app.route('/assets', methods=['GET'])
@app.route('/assets/<id>', methods=['GET'])
def assets_get(id=None):
    if not session.get("username"):
        return redirect("/login")
    
    if id:
        # Get specific asset
        asset = Asset.query.get(id)
        return jsonify({
            "id": asset.id,
            "name": asset.name,
            "location": asset.location,
            "status": asset.status,
            "count": asset.count
        })
    else:
        # Get all assets
        assets = Asset.query.all()
        asset_status_options = [status.value.removeprefix("AssetStatus.") for status in AssetStatus]
        return render_template('assets.html', assets=assets, asset_status_options=asset_status_options)

@app.route('/assets/<operation>', methods=['POST'])
def assets_post(operation=None):
    if not session.get("username"):
        return redirect("/login")
    
     # "add", "update", "delete"
    if operation == "add":
        name = request.form.get("name")
        location = request.form.get("location")
        status = request.form.get("status")
        count = request.form.get("count")

        # Ensure name is unique
        existing_asset = Asset.query.filter_by(name=name).first()
        if existing_asset:
            flash("Asset with this name already exists.", "error")
        else:
            new_asset = Asset(name=name, location=location, status=status, count = count)
            db.session.add(new_asset)
            db.session.commit()
    elif operation == "update":
        id = request.form.get("id")
        asset = Asset.query.get(id)
        if asset:
            asset.name = request.form.get("name")
            # Ensure name is unique
            existing_asset = Asset.query.filter_by(name=asset.name).first()
            if existing_asset and existing_asset.id != asset.id:
                flash("Asset with this name already exists.", "error")
                return redirect("/assets")
                
            asset.location = request.form.get("location")
            asset.status = request.form.get("status")
            asset.count = request.form.get("count")
            db.session.commit()
        else:
            flash(f"Could not update asset with ID {id}: Asset not found", "error")
    elif operation == "delete":
        id = request.form.get("id")
        asset = Asset.query.get(id)
        if asset:
            db.session.delete(asset)
            db.session.commit()
        else:
            flash(f"Could not delete asset with ID {id}: Asset not found", "error")
    else:
        flash("Invalid operation.", "error")
    return redirect("/assets")

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
    import audit # Register audit listeners
    app.run()
