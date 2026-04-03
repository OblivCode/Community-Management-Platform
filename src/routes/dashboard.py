import datetime
from flask import Blueprint, render_template, redirect, session, flash

from ..auth import check_authentication
from ..models import Asset, AssetStatus, Budget, Document, Transaction
from ..utils import CURRENCY_SYMBOLS, budget_health_threshold, get_currency_symbol
from ..services import get_exchange_rate

dashboard_bp = Blueprint('dashboard', __name__)

# Dashboard Route
@dashboard_bp.route('/dashboard')
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

    count_no_receipt = Transaction.query.filter_by(budget_id=budget.id, document_id=None).count() if budget.id else 0

    # B. Asset Overview
    count_assets = Asset.query.count()
    count_assets_damaged = Asset.query.filter(Asset.status == AssetStatus.DAMAGED).count()

    # C. Document Overview
    count_documents = Document.query.count()
    unlinked_documents = Document.query.filter_by(parent_id=None).count()

    # D. Recent transactions
    recent_transactions = Transaction.query.order_by(Transaction.timestamp.desc()).filter_by(budget_id=budget.id).limit(3).all() if budget.id else []

    # E. Convert budget totals and transaction costs to UI display currency
    ui_code = session.get('ui_currency', get_currency_symbol())
    ui_symbol = CURRENCY_SYMBOLS.get(ui_code, get_currency_symbol())
    budget_currency = (budget.currency if budget and budget.currency else None) or ui_code
    budget_rate = get_exchange_rate(budget_currency, ui_code)
    total_budget = round(budget.total_fund * budget_rate, 2)
    remaining_budget = round(budget.remaining_fund * budget_rate, 2)
    tx_ui_costs = {}
    for t in recent_transactions:
        rate = get_exchange_rate(t.currency, ui_code)
        tx_ui_costs[t.id] = round(t.cost * rate, 2)

    minimum_budget_health = budget_health_threshold * 100

    return render_template('dashboard.html',
                           username=session["username"],
                           minimum_budget_health=minimum_budget_health,
                           total_budget=total_budget,
                           remaining_budget=remaining_budget,
                           ui_symbol=ui_symbol,
                           tx_ui_costs=tx_ui_costs,
                           count_no_receipt=count_no_receipt,
                           count_assets=count_assets,
                           count_assets_damaged=count_assets_damaged,
                           count_documents=count_documents,
                           unlinked_documents=unlinked_documents,
                           recent_transactions=recent_transactions)