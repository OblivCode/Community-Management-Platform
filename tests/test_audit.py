import pytest
from src.audit import get_current_user_id
from src.models import Asset

class TestAudit:
    def test_get_current_user_id_no_context(self, test_app):
        """Validate get_current_user_id returns None outside context."""
        # Outside of a request context with session, it should be None
        assert get_current_user_id() is None

    def test_get_current_user_id_with_session(self, test_app):
        """Validate get_current_user_id returns the user id within session."""
        with test_app.test_request_context():
            from flask import session
            session["user_id"] = 123
            
            assert get_current_user_id() == 123
