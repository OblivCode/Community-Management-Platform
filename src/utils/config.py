import os

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

# Budget health threshold for warnings
budget_health_threshold = 0.2  # 20%

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}
