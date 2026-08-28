"""Date and time utilities."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.utils.constants import DEFAULT_TIMEZONE


IST_DISPLAY_FORMAT = "%d-%m-%Y %I:%M:%S %p"

_EMPTY_MARKERS = {"", "—", "None"}


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

    @staticmethod
    def format_ist(value: str | datetime | None, fmt: str = IST_DISPLAY_FORMAT) -> str:
        """Format a UTC timestamp (ISO string or datetime) as IST for display.

        Returns an em dash for missing/unparseable values, and is safe to call
        with a value that is already an em dash placeholder.
        """
        if value is None:
            return "—"
        if isinstance(value, str) and value.strip() in _EMPTY_MARKERS:
            return "—"
        try:
            dt = value if isinstance(value, datetime) else DateTimeHelper.parse_iso(value)
        except (TypeError, ValueError):
            return "—"
        return DateTimeHelper.to_local(dt).strftime(fmt)
