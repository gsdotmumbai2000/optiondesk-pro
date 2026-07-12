"""Time provider."""

from datetime import date, datetime, timezone


class TimeProvider:
    """Supply current time and trade date."""

    def now(self) -> datetime:
        """Return current UTC time."""
        return datetime.now(timezone.utc)

    def trade_date(self, moment: datetime | None = None) -> date:
        """Return trade date for a moment."""
        current = moment or self.now()
        return current.date()
