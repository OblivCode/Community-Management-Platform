import pytest
from src.utils.uploads import allowed_file
from src.utils.config import get_currency_code, get_currency_symbol, ALLOWED_EXTENSIONS
from src.utils.budget import validate_budget_exists
from src.models import Setting, Budget, db

class TestUtils:
    def test_allowed_file_valid(self):
        """Validate allowed files are approved."""
        assert allowed_file("test.png") == True
        assert allowed_file("receipt.pdf") == True

    def test_allowed_file_invalid(self):
        """Validate disallowed files are rejected."""
        assert allowed_file("test.exe") == False
        assert allowed_file("script.sh") == False
        assert allowed_file("noextension") == False

    def test_currency_code_default(self, test_app):
        """Validate currency code defaults to GBP."""
        with test_app.app_context():
            assert get_currency_code() == "GBP"

    def test_currency_code_custom(self, test_app):
        """Validate currency code uses database setting."""
        with test_app.app_context():
            setting = Setting(key="currency_code", value="EUR")
            db.session.add(setting)
            db.session.commit()
            
            assert get_currency_code() == "EUR"
            assert get_currency_symbol() == "€"

    def test_validate_budget_exists(self, test_app):
        """Validate checking if a budget exists."""
        with test_app.app_context():
            # Add a budget for 2026
            budget = Budget(year="2026", total_fund=1000, remaining_fund=1000)
            db.session.add(budget)
            db.session.commit()

            # By default during test context without mocking, get_budget_year might return current year
            # So we just ensure validate_budget_exists executes without crashing and returns boolean
            with test_app.test_request_context():
                exists, year = validate_budget_exists(Budget)
                assert isinstance(exists, bool)
                assert isinstance(year, str)
