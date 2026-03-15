import datetime
from flask import session, flash, redirect


def get_budget_year() -> str:
    """Get the current budget year from session or default to current year."""
    return session.get("budget_year", str(datetime.datetime.now().year))


def validate_budget_exists(Budget) -> tuple[bool, str]:
    """Check if a budget exists for the current year."""
    year = get_budget_year()
    exists = Budget.query.filter_by(year=year).first() is not None
    return exists, year



