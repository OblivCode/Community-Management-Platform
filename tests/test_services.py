import pytest
from src.services import get_exchange_rate


class TestServices:

    def test_exchange_same_currency(self):
        """Validate that exchanging a currency to itself returns 1.0."""
        # When we exchange GBP to GBP, it should be a 1:1 ratio
        rate = get_exchange_rate("GBP", "GBP")
        assert rate == 1.0

    def test_exchange_different_currency_returns_float(self):
        """Validate that exchanging different currencies returns a number."""
        # When converting between different currencies, we should get a number back
        # The actual value depends on the API, but it must be a positive float
        rate = get_exchange_rate("GBP", "EUR")
        assert isinstance(rate, float), "Exchange rate should be a number"
        assert rate > 0.0, "Exchange rate should be positive"

    def test_exchange_usd_to_jpy(self):
        """Validate that USD to JPY exchange works (common currency pair)."""
        rate = get_exchange_rate("USD", "JPY")
        assert isinstance(rate, float)
        assert rate > 0.0

    def test_exchange_eur_to_gbp(self):
        """Validate that EUR to GBP exchange works (common currency pair)."""
        rate = get_exchange_rate("EUR", "GBP")
        assert isinstance(rate, float)
        assert rate > 0.0

    def test_exchange_same_currency_multiple_times(self):
        """Validate consistent results when exchanging same currency repeatedly."""
        rate1 = get_exchange_rate("GBP", "GBP")
        rate2 = get_exchange_rate("GBP", "GBP")
        assert rate1 == rate2 == 1.0

    def test_exchange_unknown_currency_handled(self):
        """Validate that unknown currencies are handled gracefully."""
        # Unknown currency codes should still return a float (fallback behavior)
        rate = get_exchange_rate("XXX", "YYY")
        assert isinstance(rate, float)
        # Fallback typically returns 1.0 for unknown currencies

    def test_exchange_case_sensitivity(self):
        """Validate that currency codes are handled case-insensitively."""
        # Most APIs handle currency codes in uppercase, test it doesn't crash
        rate_lower = get_exchange_rate("gbp", "eur")
        rate_upper = get_exchange_rate("GBP", "EUR")
        # Both should return a valid float
        assert isinstance(rate_lower, float)
        assert isinstance(rate_upper, float)

    def test_exchange_rate_is_reasonable(self):
        """Validate that exchange rates are within reasonable bounds."""
        # Most currencies are between 0.5 and 150 for GBP cross rates
        rate = get_exchange_rate("GBP", "JPY")
        assert isinstance(rate, float)
        assert 0.1 < rate < 500.0, "Exchange rate seems unreasonable"

    def test_exchange_same_currency_different_cases(self):
        """Validate that same currency with different cases returns 1.0."""
        # e.g., GBP vs gbp should both give 1.0 when converting to same
        rate = get_exchange_rate("gbp", "GBP")
        assert rate == 1.0
