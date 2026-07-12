"""Holiday repository port."""

from datetime import date
from typing import Protocol, runtime_checkable

from app.market.holidays.models import Holiday, SpecialSession


@runtime_checkable
class IHolidayRepository(Protocol):
    """Persistence port for holidays and special sessions."""

    def initialize(self) -> None:
        """Load or connect to storage."""

    def close(self) -> None:
        """Release storage resources."""

    def get_holidays(self, exchange: str) -> list[Holiday]:
        """Return holidays for an exchange."""

    def get_holiday_on(self, exchange: str, on_date: date) -> Holiday | None:
        """Return a holiday on a specific date."""

    def get_special_sessions(self, exchange: str) -> list[SpecialSession]:
        """Return special sessions for an exchange."""

    def save_holiday(self, holiday: Holiday) -> None:
        """Persist a holiday."""
