import datetime, os, random
from flask import Flask, jsonify, render_template, request, session, redirect, flash
from werkzeug.security import generate_password_hash
from .auth import validate_user, check_authentication
from .models import ActionLog, AssetStatus, Document, Setting, Transaction, db, User, Budget, Asset
from .routes import auth_bp, dashboard_bp, settings_bp, assets_bp, expenses_bp, documents_bp, events_bp
from .utils import CURRENCY_SYMBOLS, UPLOAD_FOLDER, DATABASE_FOLDER, get_currency_code, get_currency_symbol, budget_health_threshold
from .services import get_exchange_rate



# TODO: Develop recent activity log for actions like asset updates, document uploads, etc.
# Temporary variables
# TODO: implement settings and map currency symbol and budget health threshold





def setup_database(app):
    with app.app_context():
        # 1. Create all tables if they don't exist
        if app.config.get('TESTING', False):
            # Drop tables to always force a fresh testing database structure on startup
            db.drop_all()
        db.create_all()

        # 2. Load persisted settings
        pass

        # 3. Check if we need to seed a Test User
        if app.config.get('TESTING', False):
            print("Creating Test Data...")

            # Create Users
            jay = User.query.filter_by(username='Jay').first()
            if not jay:
                jay = User(username='Jay', password=generate_password_hash('password123'), role='Treasurer')
                db.session.add(jay)

            skipper = User.query.filter_by(username='Skipper').first()
            if not skipper:
                skipper = User(username='Skipper', password=generate_password_hash('123'), role='Captain')
                db.session.add(skipper)

            # Create randomized budgets for last 4 years
            years = ['2026', '2025', '2024', '2023']
            fund_range = [1500, 1800]
            budget_2026 = None

            for year in years:
                b = Budget.query.filter_by(year=year).first()
                if not b:
                    total_fund = random.randrange(fund_range[0], fund_range[1])
                    b = Budget(year=year, total_fund=total_fund, remaining_fund=total_fund)
                    db.session.add(b)
                if year == str(datetime.datetime.now().year):
                    budget_2026 = b
                    
            db.session.commit()
            
            # Prefill additional data if 2026 budget exists and no assets exist
            if budget_2026 and Asset.query.count() == 0:
                from .models import AssetStatus, Event, Document, Transaction
                
                # Assets
                asset1 = Asset(name='Match Balls (Pack of 10)', location='Storage Unit A', status=AssetStatus.FINE, count=2)
                asset2 = Asset(name='Training Bibs (Blue)', location='Locker Room', status=AssetStatus.DAMAGED, count=15)
                db.session.add_all([asset1, asset2])
                
                # Event
                event1 = Event(title='Season Opener Match', description='First game of the league', date=datetime.datetime.now() - datetime.timedelta(days=5))
                event2 = Event(title='Pub Crawl Social', description='Post-training mingle', date=datetime.datetime.now() + datetime.timedelta(days=10))
                db.session.add_all([event1, event2])
                
                # Document
                doc1 = Document(note='Invoice for Match Balls', filename='Invoice for Match Balls.pdf', timestamp=datetime.datetime.now(), uploaded_by=jay.id)
                db.session.add(doc1)
                db.session.flush() # flush to get IDs for linking
                
                # Transactions
                txn1 = Transaction(cost=45.50, currency='GBP', note='Ordered match balls', timestamp=datetime.datetime.now() - datetime.timedelta(days=7), category='Equipment', author=jay.id, budget_id=budget_2026.id, document_id=doc1.id, asset_id=asset1.id)
                txn2 = Transaction(cost=120.00, currency='GBP', note='League entry fee', timestamp=datetime.datetime.now() - datetime.timedelta(days=14), category='Fees', author=jay.id, budget_id=budget_2026.id)
                db.session.add_all([txn1, txn2])
                
                # Adjust remaining fund for budget
                budget_2026.remaining_fund = budget_2026.total_fund - (txn1.cost + txn2.cost)

            # Commit to Database
            db.session.commit()
            print("Database initialized with Users and dummy test data.")

def create_app(config=None):
    app = Flask(__name__)

    # Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": 'sqlite:///' + os.path.join(basedir, 'data', 'cmp.db'),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    })
    app.config["SESSION_PERMANENT"] = False
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

    if config:
        app.config.update(config)

    # Configure database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(events_bp)

    # Register index page to login
    @app.route('/')
    def index():
        return redirect('/login')

    #
    @app.context_processor
    def inject_budget_year():
        if "budget_year" not in session:
            session["budget_year"] = str(datetime.datetime.now().year)
        budget_year = session["budget_year"]
        available_years = [str(year) for year in range(datetime.datetime.now().year + 1, 2020, -1)]
        # UI display currency (session-based, does not touch DB)
        ui_currency_code = session.get('ui_currency', get_currency_code())
        ui_currency_symbol = CURRENCY_SYMBOLS.get(ui_currency_code, '£')
        # Check if budget exists for the selected year
        budget_exists = Budget.query.filter_by(year=budget_year).first() is not None
        return dict(
            budget_year=budget_year,
            available_years=available_years,
            settings={'currency_code': get_currency_code(), 'currency': get_currency_symbol()},
            currency=get_currency_symbol(),
            currency_code=get_currency_code(),
            currency_symbols=CURRENCY_SYMBOLS,
            ui_currency_code=ui_currency_code,
            ui_currency_symbol=ui_currency_symbol,
            budget_exists=budget_exists,
        )


    # Routes that require a valid budget year for POST operations
    BUDGET_REQUIRED_POST_ROUTES = {'/expenses', '/assets', '/documents'}
    @app.before_request
    def check_budget_for_post():
        """Block POST requests to budget-dependent routes when no budget exists."""
        if request.method == 'POST' and check_authentication():
            # Check if this route requires a budget year
            path = request.path.rstrip('/')
            if path in BUDGET_REQUIRED_POST_ROUTES or path.startswith('/assets/') and path.endswith('/add'):
                budget_year = session.get("budget_year", str(datetime.datetime.now().year))
                if not Budget.query.filter_by(year=budget_year).first():
                    flash(f"Cannot perform action: No budget exists for year {budget_year}.", "error")
                    # Redirect back to the referring page or a safe default
                    return redirect(request.referrer or '/dashboard')


    return app



def main():
    app = create_app()
    # Ensure database folder exists
    os.makedirs(DATABASE_FOLDER, exist_ok=True)
    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    setup_database(app)

    # Register audit listeners
    from . import audit

    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
