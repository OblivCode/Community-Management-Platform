import datetime
from flask import Blueprint, render_template, redirect, request, session, flash

from ..auth import check_authentication
from ..models import Budget, Document, Transaction, User, db
from ..utils import CURRENCY_SYMBOLS, app_settings
from ..services import get_exchange_rate

expenses_bp = Blueprint('expenses', __name__)


@expenses_bp.route('/expenses', methods=['GET'])
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


@expenses_bp.route('/expenses', methods=['POST'])
def expenses_post():
    if not check_authentication():
        return redirect("/login")

    # Import here to avoid circular imports
    from ..app import save_upload

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


@expenses_bp.route('/expenses/<year>', methods=['GET'])
def expenses_post_year(year):
    if not check_authentication():
        return redirect("/login")
    
    # Update session budget year
    session["budget_year"] = year
    return redirect("/expenses")


@expenses_bp.route('/expenses/delete/<int:id>', methods=['POST'])
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


@expenses_bp.route('/expenses/link/<int:transaction_id>', methods=['POST'])
def expenses_link_document(transaction_id):
    if not check_authentication():
        return redirect("/login")

    # Import here to avoid circular imports
    from ..app import save_upload

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


@expenses_bp.route('/budget/set_currency', methods=['POST'])
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
