"""DTE and TTE utilities."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.utils.constants import DEFAULT_TIMEZONE


def calculate_dte(
    from_date: date,
    to_date: date,
    trading_days: set[date],
) -> int:
    """Calculate trading days to expiry (exclusive of from_date)."""
    if to_date <= from_date:
        return 0
    count = 0
    current = from_date + timedelta(days=1)
    while current <= to_date:
        if current in trading_days:
            count += 1
        current += timedelta(days=1)
    return count


def calculate_tte(
    now: datetime,
    expiry_date: date,
    market_close: time,
    *,
    timezone: str = DEFAULT_TIMEZONE,
) -> int:
    """Calculate seconds to expiry at market close."""
    tz = ZoneInfo(timezone)
    if now.tzinfo is None:
        now = now.replace(tzinfo=ZoneInfo("UTC"))
    local_now = now.astimezone(tz)
    expiry_close = datetime.combine(expiry_date, market_close, tzinfo=tz)
    if local_now >= expiry_close:
        return 0
    return int((expiry_close - local_now).total_seconds())
