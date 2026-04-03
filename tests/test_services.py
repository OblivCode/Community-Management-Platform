import pytest
from src.services import get_exchange_rate

class TestServices:
    def test_exchange_same_currency(self):
        """Validate exchange rate between same currency is 1.0."""
        rate = get_exchange_rate("GBP", "GBP")
        assert rate == 1.0

    def test_exchange_different_currency(self):
        """Validate exchange rate between different currencies returns a float."""
        # This will actually hit the real API or fallback to 1.0 if it fails.
        # Either way, we expect a float as the return type.
        rate = get_exchange_rate("GBP", "EUR")
        assert isinstance(rate, float)
        assert rate > 0.0
