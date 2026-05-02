import os
import shutil

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
)

from ..auth import check_authentication
from ..models import Setting, User, db
from ..utils import CURRENCY_SYMBOLS, get_currency_code, get_currency_symbol
from ..utils.config import UPLOAD_FOLDER

settings_bp = Blueprint("settings", __name__)


# Settings Route
@settings_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if not check_authentication():
        return redirect("/login")

    if request.method == "POST":
        new_code = request.form.get("currency_code", "GBP")
        if new_code not in CURRENCY_SYMBOLS:
            new_code = "GBP"
        # Persist to Setting table
        row = Setting.query.filter_by(key="currency_code").first()
        if row:
            row.value = new_code
        else:
            db.session.add(Setting(key="currency_code", value=new_code))
        db.session.commit()

        # update the ui_currency session variable so it reflects instantly!
        session["ui_currency"] = new_code

        flash("General settings updated.", "success")
        return redirect("/settings")

    user = User.query.filter_by(username=session["username"]).first()
    return render_template(
        "settings.html", user=user, currency_symbols=CURRENCY_SYMBOLS
    )


@settings_bp.route("/settings/user", methods=["POST"])
def settings_user():
    if not check_authentication():
        return redirect("/login")

    theme = request.form.get("theme")
    if theme in ["light", "dark"]:
        session["theme"] = theme
        flash("Theme updated.", "success")

    return redirect("/settings")


@settings_bp.route("/set_ui_currency", methods=["POST"])
def set_ui_currency():
    """Store the user's preferred display currency in the session (no DB write)."""
    if not check_authentication():
        return redirect("/login")

    code = request.form.get("ui_currency", get_currency_code())
    if code in CURRENCY_SYMBOLS:
        session["ui_currency"] = code
    return redirect(request.referrer or "/dashboard")


@settings_bp.route("/set_year", methods=["POST"])
def set_year():
    if not check_authentication():
        return redirect("/login")

    year = request.form.get("year")
    if year:
        session["budget_year"] = year

    return redirect(request.referrer or "/dashboard")


@settings_bp.route("/settings/admin/reset", methods=["POST"])
def admin_reset():
    """Wipe database and reseed with demo data. Prototype feature only."""
    if not check_authentication():
        return redirect("/login")

    # Optional role check (uncomment if required)
    # user = User.query.get(session.get("user_id"))
    # if not user or user.role not in ["Treasurer", "Captain", "Admin"]:
    #     flash("Unauthorized.", "error")
    #     return redirect("/settings")

    confirm = request.form.get("confirm_reset")
    if confirm != "RESET":
        flash("Please type RESET to confirm.", "error")
        return redirect("/settings")

    # Wipe and reseed DB using the same setup logic from app.py
    # We must import setup_database here to avoid circular imports at the top
    from ..app import setup_database

    try:
        setup_database(current_app, drop_all=True, seed_demo_data=True)

        # Clear uploads folder
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")

        flash("Application reset successfully. Demo data restored.", "success")

        # We should log out the user so they can log back in as Jay or Skipper
        session.clear()
        return redirect("/login")

    except Exception as e:
        flash(f"Error during reset: {e}", "error")
        return redirect("/settings")
