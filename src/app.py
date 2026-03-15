import datetime
import os
import requests as http_requests
from flask import Flask, jsonify, render_template, request, session, redirect, flash
from werkzeug.utils import secure_filename
from .auth import validate_user, check_authentication
from .models import ActionLog, AssetStatus, Document, Setting, Transaction, db, User, Budget, Asset
from .routes import auth_bp, dashboard_bp


app = Flask(__name__)


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload(file) -> str | None:
    """Save an uploaded file to UPLOAD_FOLDER. Returns the filename or None on failure."""
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        return filename
    return None



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
    # UI display currency (session-based, does not touch DB)
    ui_currency_code = session.get('ui_currency', app_settings['currency_code'])
    ui_currency_symbol = CURRENCY_SYMBOLS.get(ui_currency_code, '£')
    return dict(
        budget_year=budget_year,
        available_years=available_years,
        settings=app_settings,
        currency=app_settings['currency'],
        currency_code=app_settings['currency_code'],
        currency_symbols=CURRENCY_SYMBOLS,
        ui_currency_code=ui_currency_code,
        ui_currency_symbol=ui_currency_symbol,
    )


# TODO: Develop recent activity log for actions like asset updates, document uploads, etc.
# Temporary variables
# TODO: implement settings and map currency symbol and budget health threshold
budget_health_threshold = 0.2 # 20%



@app.route('/')
def index():
    return redirect('/login')


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

@app.route('/set_ui_currency', methods=['POST'])
def set_ui_currency():
    """Store the user's preferred display currency in the session (no DB write)."""
    if not check_authentication():
        return redirect("/login")
    code = request.form.get('ui_currency', app_settings['currency_code'])
    if code in CURRENCY_SYMBOLS:
        session['ui_currency'] = code
    return redirect(request.referrer or '/dashboard')

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
            asset_image = request.files.get("asset_image")
            asset_filename = save_upload(asset_image) if asset_image and asset_image.filename else None
            new_asset = Asset(name=name, location=location, status=status, count=count, filename=asset_filename)
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
            asset_image = request.files.get("asset_image")
            if asset_image and asset_image.filename:
                saved = save_upload(asset_image)
                if saved:
                    asset.filename = saved
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
        transactions = Transaction.query.filter_by(budget_id=budget.id).all()
        count_no_receipt = Transaction.query.filter_by(budget_id=budget.id, document_id=None).count()
    else:
        budget = Budget(year=year, total_fund=0.0, remaining_fund=0.0)
        flash(f"No budget found for year {year}. Showing empty budget.", "info")

    # Determine UI currency and convert budget totals for display
    ui_code = session.get('ui_currency', app_settings['currency_code'])
    budget_currency = budget.currency if hasattr(budget, 'currency') and budget.currency else app_settings['currency_code']
    ui_symbol = CURRENCY_SYMBOLS.get(ui_code, '£')
    ui_rate = get_exchange_rate(budget_currency, ui_code)
    ui_total_fund = round(budget.total_fund * ui_rate, 2)
    ui_remaining_fund = round(budget.remaining_fund * ui_rate, 2)

    # Pre-convert each transaction cost to UI currency
    tx_ui_costs = {}
    for t in transactions:
        rate = get_exchange_rate(t.currency, ui_code)
        tx_ui_costs[t.id] = round(t.cost * rate, 2)

    # Get all documents for the link receipt modal
    documents = Document.query.all()

    return render_template(
        'expenses.html',
        transactions=transactions,
        budget=budget,
        budget_currency=budget_currency,
        count_no_receipt=count_no_receipt,
        documents=documents,
        username=session["username"],
        currency_symbols=CURRENCY_SYMBOLS,
        ui_total_fund=ui_total_fund,
        ui_remaining_fund=ui_remaining_fund,
        ui_symbol=ui_symbol,
        tx_ui_costs=tx_ui_costs,
    )

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
        saved_name = save_upload(receipt_file)
        if saved_name:
            new_doc = Document(
                note=f"Receipt: {note}",
                filename=saved_name,
                timestamp=timestamp,
                uploaded_by=user.id,
            )
            db.session.add(new_doc)
            db.session.flush()  # get the new ID before commit
            document_id = new_doc.id
        else:
            flash("Invalid file type for receipt. Allowed: images and PDF.", "warning")
            document_id = None
    elif document_id:
        doc = Document.query.get(document_id)
        if not doc:
            flash("Document ID not found.", "error")
            return redirect("/expenses")

    # Convert cost to budget's own currency for deduction
    budget = Budget.query.get(budget_id)
    budget_currency = (budget.currency if budget and budget.currency else None) or app_settings['currency_code']
    rate = get_exchange_rate(currency_code, budget_currency)
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

    # Deduct from budget (cost_in_default is already in budget_currency)
    if budget:
        budget.remaining_fund = round(budget.remaining_fund - cost_in_default, 2)

    db.session.add(new_transaction)
    db.session.commit()
    return redirect("/expenses?prompt_asset=1")

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
        # Refund cost back to budget in budget currency
        budget = transaction.budget
        if budget:
            budget_currency = budget.currency or app_settings['currency_code']
            refund_rate = get_exchange_rate(transaction.currency, budget_currency)
            refund = round(transaction.cost * refund_rate, 2)
            budget.remaining_fund = round(budget.remaining_fund + refund, 2)
        db.session.delete(transaction)
        db.session.commit()
        flash("Transaction deleted and amount refunded to budget.", "success")
    else:
        flash("Transaction not found.", "error")
    return redirect("/expenses")

@app.route('/expenses/link/<int:transaction_id>', methods=['POST'])
def expenses_link_document(transaction_id):
    if not check_authentication():
        return redirect("/login")

    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        flash("Transaction not found.", "error")
        return redirect("/expenses")

    user = User.query.filter_by(username=session["username"]).first()
    receipt_file = request.files.get("receipt_file")
    document_id = request.form.get("document_id") or None

    if receipt_file and receipt_file.filename != "":
        saved_name = save_upload(receipt_file)
        if saved_name:
            new_doc = Document(
                note=f"Receipt for transaction #{transaction_id}",
                filename=saved_name,
                timestamp=datetime.datetime.now(),
                uploaded_by=user.id,
            )
            db.session.add(new_doc)
            db.session.flush()
            document_id = new_doc.id
        else:
            flash("Invalid file type. Allowed: images and PDF.", "warning")
            return redirect("/expenses")
    elif document_id:
        doc = Document.query.get(document_id)
        if not doc:
            flash("Document not found.", "error")
            return redirect("/expenses")
    else:
        flash("Please select a document or upload a receipt file.", "error")
        return redirect("/expenses")

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
        saved_name = save_upload(file)
        if saved_name:
            new_document = Document(
                note=note,
                timestamp=timestamp,
                filename=saved_name,
                uploaded_by=uploader.id,
            )
            db.session.add(new_document)
            db.session.commit()
            flash("Document uploaded successfully.", "success")
        else:
            flash("Invalid file type. Allowed: images (png, jpg, gif, webp) and PDF.", "error")
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

@app.route('/budget/set_currency', methods=['POST'])
def budget_set_currency():
    """Update the stored currency of a budget (affects how fund amounts are interpreted)."""
    if not check_authentication():
        return redirect("/login")
    budget_id = request.form.get("budget_id")
    new_currency = request.form.get("budget_currency")
    if budget_id and new_currency in CURRENCY_SYMBOLS:
        budget = Budget.query.get(budget_id)
        if budget:
            budget.currency = new_currency
            db.session.commit()
            flash(f"Budget currency set to {new_currency}.", "success")
        else:
            flash("Budget not found.", "error")
    else:
        flash("Invalid currency selection.", "error")
    return redirect("/expenses")

def setup_database():
    with app.app_context():
        # 1. Create all tables if they don't exist
        db.create_all()

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
    
    

    # Configure session to expire on browser close
    app.config["SESSION_PERMANENT"] = False
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
    
    # Configure database
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data', 'cmp.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    setup_database()
    from . import audit # Register audit listeners

    # Configure image uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
