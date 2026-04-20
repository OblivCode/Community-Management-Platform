"""Routes package"""
from .auth import auth_bp
from .dashboard import dashboard_bp
from .settings import settings_bp
from .assets import assets_bp
from .expenses import expenses_bp
from .documents import documents_bp
from .events import events_bp
from .links import links_bp

__all__ = [
    'auth_bp',
    'dashboard_bp',
    'settings_bp',
    'assets_bp',
    'expenses_bp',
    'documents_bp',
    'events_bp',
    'links_bp',
]
