"""Routes package - Flask Blueprints for route organization."""
from .auth_routes import auth_bp
from .dashboard import dashboard_bp

__all__ = ['auth_bp', 'dashboard_bp']
