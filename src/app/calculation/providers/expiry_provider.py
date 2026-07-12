"""Expiry provider."""

from datetime import date, datetime
from decimal import Decimal

from app.calculation.exceptions import InvalidExpiryException
from app.calculation.providers.ports import IExpiryCalendarPort
from app.calculation.utilities.time_utils import calculate_fractional_year


class ExpiryProvider:
    """Supply expiry timing inputs."""

    def __init__(self, calendar: IExpiryCalendarPort) -> None:
        """Initialize provider."""
        self._calendar = calendar

    def parse_expiry(self, expiry: str | date) -> date:
        """Parse expiry into a date."""
        if isinstance(expiry, date):
            return expiry
        text = expiry.strip()
        for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        raise InvalidExpiryException(f"Unsupported expiry format: {expiry}")

    def days_to_expiry(
        self,
        exchange: str,
        from_date: date,
        expiry_date: date,
    ) -> int:
        """Return trading days to expiry."""
        return self._calendar.calculate_dte(exchange, from_date, expiry_date)

    def time_to_expiry(
        self,
        exchange: str,
        now: datetime,
        expiry_date: date,
    ) -> Decimal:
        """Return fractional year time to expiry."""
        seconds = self._calendar.calculate_tte_seconds(exchange, now, expiry_date)
        return calculate_fractional_year(seconds)
