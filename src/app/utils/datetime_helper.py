"""Date and time utilities."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.utils.constants import DEFAULT_TIMEZONE


class DateTimeHelper:
    """Helper for consistent UTC and IST datetime handling."""

    @staticmethod
    def utc_now() -> datetime:
        """Return the current UTC datetime."""
        return datetime.now(UTC)

    @staticmethod
    def utc_now_iso() -> str:
        """Return the current UTC datetime as an ISO-8601 string."""
        return DateTimeHelper.utc_now().isoformat()

    @staticmethod
    def to_utc(value: datetime) -> datetime:
        """Convert a datetime to UTC."""
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def to_local(value: datetime, timezone: str = DEFAULT_TIMEZONE) -> datetime:
        """Convert a datetime to the configured local timezone."""
        utc_value = DateTimeHelper.to_utc(value)
        return utc_value.astimezone(ZoneInfo(timezone))

    @staticmethod
    def parse_iso(value: str) -> datetime:
        """Parse an ISO-8601 datetime string."""
        return datetime.fromisoformat(value)
