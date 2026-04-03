import os

from ..models import Setting, db

# Supported currencies: code -> symbol
CURRENCY_SYMBOLS = {
    'GBP': '£', 'USD': '$', 'EUR': '€', 'AUD': 'A$',
    'CAD': 'C$', 'JPY': '¥', 'INR': '₹',
}

def get_currency_code():
    """Fetches the current currency setting from the DB and returns the code."""
    setting = Setting.query.filter_by(key="currency_code").first()
    return setting.value if setting else "GBP"

def get_currency_symbol():
    """Fetches the current currency setting from the DB and returns the symbol."""
    code = get_currency_code()
    return CURRENCY_SYMBOLS.get(code, "£")

# Budget health threshold for warnings
budget_health_threshold = 0.2  # 20%

# File upload configuration
DATABASE_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}