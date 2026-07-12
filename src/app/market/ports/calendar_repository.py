"""Calendar repository port."""

from typing import Protocol, runtime_checkable

from app.market.calendar.models import MarketCalendarConfig
from app.market.sessions.models import TradingSession


@runtime_checkable
class ICalendarRepository(Protocol):
    """Persistence port for calendar config and trading sessions."""

    def initialize(self) -> None:
        """Load or connect to storage."""

    def close(self) -> None:
        """Release storage resources."""

    def get_calendar_config(self, exchange: str) -> MarketCalendarConfig | None:
        """Return calendar configuration for an exchange."""

    def get_sessions(self, exchange: str) -> list[TradingSession]:
        """Return trading sessions for an exchange."""

    def save_session(self, session: TradingSession) -> None:
        """Persist a trading session."""
