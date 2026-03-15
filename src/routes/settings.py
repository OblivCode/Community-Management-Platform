from flask import Blueprint, render_template, redirect, request, session, flash

from ..auth import check_authentication
from ..models import Setting, User, db
from ..utils import CURRENCY_SYMBOLS, app_settings

settings_bp = Blueprint('settings', __name__)


# Settings Route
@settings_bp.route('/settings', methods=['GET', 'POST'])
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


@settings_bp.route('/settings/user', methods=['POST'])
def settings_user():
    if not check_authentication():
        return redirect("/login")
    
    theme = request.form.get('theme')
    if theme in ['light', 'dark']:
        session['theme'] = theme
        flash("Theme updated.", "success")
    
    return redirect('/settings')


@settings_bp.route('/set_ui_currency', methods=['POST'])
def set_ui_currency():
    """Store the user's preferred display currency in the session (no DB write)."""
    if not check_authentication():
        return redirect("/login")
    
    code = request.form.get('ui_currency', app_settings['currency_code'])
    if code in CURRENCY_SYMBOLS:
        session['ui_currency'] = code
    return redirect(request.referrer or '/dashboard')


@settings_bp.route('/set_year', methods=['POST'])
def set_year():
    if not check_authentication():
        return redirect("/login")
    
    year = request.form.get("year")
    if year:
        session["budget_year"] = year
        
    return redirect(request.referrer or '/dashboard')
