"""Holiday manager."""

from datetime import date, timedelta

from app.market.enums import SessionType, Weekday
from app.market.holidays.models import Holiday, SpecialSession
from app.market.ports.holiday_repository import IHolidayRepository


class HolidayManager:
    """Manage trading holidays and special sessions."""

    def __init__(self, repository: IHolidayRepository) -> None:
        """Initialize holiday manager."""
        self._repository = repository

    def is_weekend(
        self, on_date: date, *, weekend_days: list[str] | None = None
    ) -> bool:
        """Return whether a date falls on a weekend."""
        days = weekend_days or ["SATURDAY", "SUNDAY"]
        weekday = Weekday(on_date.strftime("%A").upper())
        return weekday.value in days

    def is_trading_holiday(self, exchange: str, on_date: date) -> bool:
        """Return whether a date is a full trading holiday."""
        holiday = self._repository.get_holiday_on(exchange, on_date)
        return holiday is not None and holiday.holiday_type == "FULL"

    def is_trading_day(self, exchange: str, on_date: date) -> bool:
        """Return whether a date is a trading day."""
        if self.is_weekend(on_date):
            return False
        if self.is_trading_holiday(exchange, on_date):
            return False
        return True

    def get_holidays(self, exchange: str) -> list[Holiday]:
        """Return all holidays for an exchange."""
        return self._repository.get_holidays(exchange)

    def get_special_session(
        self, exchange: str, on_date: date
    ) -> SpecialSession | None:
        """Return a special session on a date if present."""
        for session in self._repository.get_special_sessions(exchange):
            if session.session_date == on_date:
                return session
        return None

    def is_muhurat_session(self, exchange: str, on_date: date) -> bool:
        """Return whether a date has a muhurat session."""
        session = self.get_special_session(exchange, on_date)
        return session is not None and session.session_type == SessionType.MUHURAT

    def next_trading_day(self, exchange: str, from_date: date) -> date:
        """Return the next trading day after a date."""
        current = from_date + timedelta(days=1)
        while not self.is_trading_day(exchange, current):
            current += timedelta(days=1)
        return current

    def previous_trading_day(self, exchange: str, from_date: date) -> date:
        """Return the previous trading day before a date."""
        current = from_date - timedelta(days=1)
        while not self.is_trading_day(exchange, current):
            current -= timedelta(days=1)
        return current

    def shift_for_holiday(self, exchange: str, expiry_date: date) -> date:
        """Shift expiry to previous trading day if it falls on a holiday."""
        if self.is_trading_day(exchange, expiry_date):
            return expiry_date
        return self.previous_trading_day(exchange, expiry_date)
