import datetime
import requests as http_requests
from flask import Flask, jsonify, render_template, request, session, redirect, flash
from flask_migrate import Migrate, upgrade
from auth import validateUser
from models import ActionLog, AssetStatus, Document, Setting, Transaction, db, User, Budget, Asset
import os

app = Flask(__name__)

# Configure session to expire on browser close
app.config["SESSION_PERMANENT"] = False 
app.secret_key = 'secret'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cmp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# Supported currencies: code -> symbol
CURRENCY_SYMBOLS = {
    'GBP': '£',
    'USD': '$',
    'EUR': '€',
    'AUD': 'A$',
    'CAD': 'C$',
    'JPY': '¥',
    'INR': '₹',
}

# Global settings (loaded from DB at startup)
app_settings = {
    "currency_code": "GBP",
    "currency": "£",
}

# Exchange rate cache: {base_code: {"rates": {...}, "fetched_at": datetime}}
_exchange_cache: dict = {}

def get_exchange_rate(from_code: str, to_code: str) -> float:
    """Return exchange rate from_code -> to_code using open.er-api.com. Cached for 1 hour."""
    if from_code == to_code:
        return 1.0
    now = datetime.datetime.utcnow()
    cache = _exchange_cache.get(from_code)
    if not cache or (now - cache['fetched_at']).total_seconds() > 3600:
        try:
            resp = http_requests.get(f'https://open.er-api.com/v6/latest/{from_code}', timeout=5)
            data = resp.json()
            if data.get('result') == 'success':
                _exchange_cache[from_code] = {'rates': data['rates'], 'fetched_at': now}
        except Exception as e:
            print(f'[EXCHANGE] Rate fetch failed: {e}')
            return 1.0
    rates = _exchange_cache.get(from_code, {}).get('rates', {})
    return rates.get(to_code, 1.0)

@app.context_processor
def inject_budget_year():
    if "budget_year" not in session:
        session["budget_year"] = str(datetime.datetime.now().year)
    budget_year = session["budget_year"]
    available_years = [str(year) for year in range(datetime.datetime.now().year + 1, 2020, -1)]
    return dict(
        budget_year=budget_year,
        available_years=available_years,
        settings=app_settings,
        currency=app_settings['currency'],
        currency_code=app_settings['currency_code'],
        currency_symbols=CURRENCY_SYMBOLS,
    )


# TODO: Develop recent activity log for actions like asset updates, document uploads, etc.
# Temporary variables
# TODO: implement settings and map currency symbol and budget health threshold
budget_health_threshold = 0.2 # 20%

def check_authentication():
    if not session.get("username"):
        return False

    user = User.query.filter_by(username=session["username"]).first()
    if not user or user.password != session.get("password"):
        return False
    
    return True


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():  
    if request.method == "POST":
        # Check if session exists, else get from form
        if check_authentication():
            username = session["username"]
            password = session["password"]
        else:
            username = request.form.get("username")
            password = request.form.get("password")
        
        valid = validateUser(username, password)

        if valid:
            session["username"] = username
            session["password"] = password
            session["budget_year"] = str(datetime.datetime.now().year)
            return redirect("/dashboard")
        else:
            flash("Invalid username or password", "error")
            return render_template('login.html')
    elif request.method == "GET":
        if check_authentication():
            return redirect("/dashboard")
        return render_template('login.html')
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# Dashboard Route
@app.route('/dashboard')
def dashboard():
    if not check_authentication():
        return redirect("/login")

    budget_year = session.get("budget_year", str(datetime.datetime.now().year))
    
    # 1. Build Dashboard
    # A. Budget/Expense Overview
    budget = Budget.query.filter_by(year=budget_year).first()
    if not budget:
        budget = Budget(year=budget_year, total_fund=0, remaining_fund=0)
        flash(f"No budget found for year {budget_year}.", "info")

    total_budget = budget.total_fund
    remaining_budget = budget.remaining_fund
    count_no_receipt = Transaction.query.filter_by(budget_id=budget.id, document_id=None).count() if budget.id else 0
    
    # B. Asset Overview
    count_assets = Asset.query.count()
    count_assets_damaged = Asset.query.filter(Asset.status == AssetStatus.DAMAGED).count()

    # C. Document Overview
    count_documents = Document.query.count()
    unlinked_documents = Document.query.filter_by(parent_id=None).count()
    
    # D. Action log
    recent_transactions = Transaction.query.order_by(Transaction.timestamp.desc()).filter_by(budget_id=budget.id).limit(3).all() if budget.id else []
    
    minimum_budget_health = budget_health_threshold * 100
    
    return render_template('dashboard.html', 
                           username=session["username"],
                           minimum_budget_health=minimum_budget_health,
                           total_budget=total_budget,
                           remaining_budget=remaining_budget,
                           count_no_receipt=count_no_receipt,
                           count_assets=count_assets,
                           count_assets_damaged=count_assets_damaged,
                           count_documents=count_documents,
                           unlinked_documents=unlinked_documents,
                            recent_transactions=recent_transactions)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not check_authentication():
        return redirect("/login")
    
    if request.method == 'POST':
        new_code = request.form.get('currency_code', 'GBP')
        if new_code not in CURRENCY_SYMBOLS:
            new_code = 'GBP'
        app_settings['currency_code'] = new_code
        app_settings['currency'] = CURRENCY_SYMBOLS[new_code]
        # Persist to Setting table
        row = Setting.query.filter_by(key='currency_code').first()
        if row:
            row.value = new_code
        else:
            db.session.add(Setting(key='currency_code', value=new_code))
        db.session.commit()
        flash("General settings updated.", "success")
        return redirect('/settings')
    
    user = User.query.filter_by(username=session["username"]).first()
    return render_template('settings.html', user=user, currency_symbols=CURRENCY_SYMBOLS)

@app.route('/settings/user', methods=['POST'])
def settings_user():
    if not check_authentication():
        return redirect("/login")
    
    theme = request.form.get('theme')
    if theme in ['light', 'dark']:
        session['theme'] = theme
        flash("Theme updated.", "success")
    
    return redirect('/settings')

@app.route('/set_year', methods=['POST'])
def set_year():
    if not check_authentication():
        return redirect("/login")
    
    year = request.form.get("year")
    if year:
        session["budget_year"] = year
        
    return redirect(request.referrer or '/dashboard')

# Asset Management Route

@app.route('/assets', methods=['GET'])
@app.route('/assets/<id>', methods=['GET'])
def assets_get(id=None):
    if not check_authentication():
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
        asset_status_options = [status.value for status in AssetStatus]
        return render_template('assets.html', assets=assets, asset_status_options=asset_status_options)

@app.route('/assets/<operation>', methods=['POST'])
def assets_post(operation=None):
    if not check_authentication():
        return redirect("/login")
    
     # "add", "update", "delete"
    if operation == "add":
        name = request.form.get("name")
        location = request.form.get("location")
        status_str = request.form.get("status")
        status = AssetStatus(status_str) if status_str else AssetStatus.FINE
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
            status_str = request.form.get("status")
            asset.status = AssetStatus(status_str) if status_str else AssetStatus.FINE
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

# Expense Management Route
@app.route('/expenses', methods=['GET'])
def expenses_get(year=None):
    if not check_authentication():
        return redirect("/login")
    
    year = session["budget_year"] or str(datetime.datetime.now().year)
    
    
    # Get budget for the year
    budget = Budget.query.filter_by(year=year).first()
    transactions = []
    count_no_receipt = 0
    if budget:
        # Get all transactions for the budget
        transactions = Transaction.query.filter_by(budget_id=budget.id).all()
        # Get transactions without document/receipt
        count_no_receipt = Transaction.query.filter_by(budget_id=budget.id, document_id=None).count()
    else:
        budget = Budget(year=year, total_fund=0.0, remaining_fund=0.0)
        flash(f"No budget found for year {year}. Showing empty budget.", "info")
    
    # Get all documents for the link receipt modal
    documents = Document.query.all()
    
    return render_template('expenses.html', transactions=transactions, budget=budget, count_no_receipt=count_no_receipt, documents=documents, username=session["username"], currency_symbols=CURRENCY_SYMBOLS)

@app.route('/expenses', methods=['POST'])
def expenses_post():
    if not check_authentication():
        return redirect("/login")

    # Get form data
    timestamp = datetime.datetime.now()
    note = request.form.get("note") or ""
    category = request.form.get("category") or "Uncategorized"
    cost = float(request.form.get("cost") or 0.0) 
    budget_id = int(request.form.get("budget_id")) # Mandatory
    user = User.query.filter_by(username=session["username"]).first() # Mandatory

    if not user or not budget_id:
        flash("Missing required fields.", "error")
        return redirect("/expenses")

    currency_code = request.form.get("currency_code") or app_settings['currency_code']
    if currency_code not in CURRENCY_SYMBOLS:
        currency_code = app_settings['currency_code']

    document_id = request.form.get("document_id") or None
    receipt_file = request.files.get("receipt_file")

    if receipt_file and receipt_file.filename != "":
        # TODO: Documents upload post
        document_id = None  # ignore document_id if file also provided
    elif document_id:
        doc = Document.query.get(document_id)
        if not doc:
            flash("Document ID not found.", "error")
            return redirect("/expenses")

    # Convert cost to default currency for budget deduction
    default_code = app_settings['currency_code']
    rate = get_exchange_rate(currency_code, default_code)
    cost_in_default = round(cost * rate, 2)

    # Create new transaction
    new_transaction = Transaction(
        cost=cost,
        currency=currency_code,
        note=note,
        timestamp=timestamp,
        category=category,
        author=user.id,
        budget_id=budget_id,
        document_id=document_id,
    )

    # Deduct from budget
    budget = Budget.query.get(budget_id)
    if budget:
        budget.remaining_fund = round(budget.remaining_fund - cost_in_default, 2)

    db.session.add(new_transaction)
    db.session.commit()
    return redirect("/expenses")

@app.route('/expenses/<year>', methods=['GET'])
def expenses_post_year(year):
    if not check_authentication():
        return redirect("/login")
    
    # Update session budget year
    session["budget_year"] = year
    return redirect("/expenses")

@app.route('/expenses/delete/<int:id>', methods=['POST'])
def expenses_delete(id):
    if not check_authentication():
        return redirect("/login")
    
    transaction = Transaction.query.get(id)
    if transaction:
        db.session.delete(transaction)
        db.session.commit()
        flash("Transaction deleted successfully.", "success")
    else:
        flash("Transaction not found.", "error")
    return redirect("/expenses")

@app.route('/expenses/link/<int:transaction_id>', methods=['POST'])
def expenses_link_document(transaction_id):
    if not check_authentication():
        return redirect("/login")
    
    transaction = Transaction.query.get(transaction_id)
    document_id = request.form.get("document_id")
    
    if not transaction:
        flash("Transaction not found.", "error")
        return redirect("/expenses")
    
    if not document_id:
        flash("Please select a document to link.", "error")
        return redirect("/expenses")
    
    document = Document.query.get(document_id)
    if not document:
        flash("Document not found.", "error")
        return redirect("/expenses")
    
    # Link the document to the transaction
    transaction.document_id = document_id
    db.session.commit()
    flash("Receipt linked successfully.", "success")
    return redirect("/expenses")

# Document Management Route
@app.route('/documents', methods=['GET'])
def documents_get():
    if not check_authentication():
        return redirect("/login")
    
    documents = Document.query.all()
    return render_template('documents.html', documents=documents, username=session["username"])

@app.route('/documents/<int:id>', methods=['GET'])
def documents_get_view(id):
    if not check_authentication():
        return redirect("/login")

    document = Document.query.get(id)
    if document:
        return render_template('view_document.html', document=document, username=session["username"])
    else:
        flash("Document not found.", "error")
        return redirect("/documents")


@app.route('/documents', methods=['POST'])
def documents_post():
    if not check_authentication():
        return redirect("/login")
    
    # Get form data
    file = request.files.get("document_file")
    note = request.form.get("document_note") or (file.filename if file else "")
    timestamp = datetime.datetime.now()
    uploader = User.query.filter_by(username=session["username"]).first()

    if file and file.filename != "":
        # TODO: Documents upload post (save file to disk)
        # Create new document record
        new_document = Document(
            note=note,
            timestamp=timestamp,
            filename=file.filename,
            uploaded_by=uploader.id,
        )
        db.session.add(new_document)
        db.session.commit()
        flash("Document uploaded successfully.", "success")
    else:
        flash("No file selected.", "error")
    return redirect("/documents")

@app.route('/documents/delete/<int:id>', methods=['POST'])
def documents_post_delete(id):
    if not check_authentication():
        return redirect("/login")

    document = Document.query.get(id)
    if document:
        db.session.delete(document)
        db.session.commit()
        flash("Document deleted successfully.", "success")
    else:
        flash("Document not found.", "error")
    return redirect("/documents")

@app.route('/documents/update/<id>', methods=['POST'])
def documents_post_update(id):
    if not check_authentication():
        return redirect("/login")

    document = Document.query.get(id)

    if document:
        document.note = request.form.get("document_note")
        db.session.commit()
        flash("Document updated successfully.", "success")
    else:
        flash("Document not found.", "error")
    return redirect(f"/documents/{id}")

def setup_database():
    with app.app_context():
        # 1. Apply any pending migrations (replaces bare db.create_all)
        upgrade()

        # 2. Load persisted settings
        row = Setting.query.filter_by(key='currency_code').first()
        if row and row.value in CURRENCY_SYMBOLS:
            app_settings['currency_code'] = row.value
            app_settings['currency'] = CURRENCY_SYMBOLS[row.value]

        # 3. Check if we need to seed a Test User
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

def main():
    setup_database()
    import audit # Register audit listeners
    app.run()

if __name__ == '__main__':
    main()
