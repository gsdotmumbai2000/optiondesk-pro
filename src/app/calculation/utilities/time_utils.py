"""Time utility functions."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal

SECONDS_PER_YEAR = Decimal("31557600")


def calculate_days_to_expiry(from_date: date, expiry_date: date) -> int:
    """Calculate calendar days to expiry (non-negative)."""
    delta = (expiry_date - from_date).days
    return max(delta, 0)


def calculate_time_to_expiry_seconds(
    now: datetime,
    expiry_date: date,
    *,
    market_close: time = time(15, 30),
) -> int:
    """Calculate seconds from now to expiry at market close."""
    expiry_close = datetime.combine(expiry_date, market_close, tzinfo=now.tzinfo)
    if now >= expiry_close:
        return 0
    return int((expiry_close - now).total_seconds())


def calculate_fractional_year(seconds_to_expiry: int) -> Decimal:
    """Convert seconds to expiry into fractional years."""
    if seconds_to_expiry <= 0:
        return Decimal("0")
    return Decimal(seconds_to_expiry) / SECONDS_PER_YEAR
