import datetime, os, random
from flask import Flask, jsonify, render_template, request, session, redirect, flash
from .auth import validate_user, check_authentication
from .models import ActionLog, AssetStatus, Document, Setting, Transaction, db, User, Budget, Asset
from .routes import auth_bp, dashboard_bp, settings_bp, assets_bp, expenses_bp, documents_bp
from .utils import CURRENCY_SYMBOLS, UPLOAD_FOLDER, app_settings, budget_health_threshold
from .services import get_exchange_rate



# TODO: Develop recent activity log for actions like asset updates, document uploads, etc.
# Temporary variables
# TODO: implement settings and map currency symbol and budget health threshold





def setup_database(app):
    with app.app_context():
        # 1. Create all tables if they don't exist
        db.create_all()

        # 2. Load persisted settings
        row = Setting.query.filter_by(key='currency_code').first()
        if row and row.value in CURRENCY_SYMBOLS:
            app_settings['currency_code'] = row.value
            app_settings['currency'] = CURRENCY_SYMBOLS[row.value]

        # 3. Check if we need to seed a Test User
        if app.config.get('TESTING', False):
            print("⚡ Creating Test Data...")
            
            # Create Users
            if not User.query.filter_by(username='Jay').first():
                jay = User(username='Jay', password='password123', role='Treasurer')
                db.session.add(jay)
            
            if not User.query.filter_by(username='Skipper').first():
                skipper = User(username='Skipper', password='123', role='Captain')#
                db.session.add(skipper)
            
            # Create randomized budgets for last 4 years
            years = ['2026', '2025', '2024', '2023']
            fund_range = [1500, 1800]
            
            for year in years:
                if not Budget.query.filter_by(year=year).first():
                    total_fund = random.randrange(fund_range[0], fund_range[1])
                    budget = Budget(year=year, total_fund=total_fund, remaining_fund=total_fund)
                    db.session.add(budget)
            
            # Commit to Database
            db.session.commit()
            print("✅ Database initialized with Users: Jay (Treasurer) & Skipper (Captain)")

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
        ui_currency_code = session.get('ui_currency', app_settings['currency_code'])
        ui_currency_symbol = CURRENCY_SYMBOLS.get(ui_currency_code, '£')
        # Check if budget exists for the selected year 
        budget_exists = Budget.query.filter_by(year=budget_year).first() is not None
        return dict(
            budget_year=budget_year,
            available_years=available_years,
            settings=app_settings,
            currency=app_settings['currency'],
            currency_code=app_settings['currency_code'],
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

    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    setup_database(app)

    # Register audit listeners
    from . import audit
   
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
