"""Market calendar."""

from datetime import date, datetime, time

from app.market.calendar.models import MarketCalendarConfig
from app.market.enums import SessionType
from app.market.holidays.holiday_manager import HolidayManager
from app.market.ports.calendar_repository import ICalendarRepository
from app.market.sessions.models import TradingSession
from app.utils.constants import DEFAULT_TIMEZONE


class MarketCalendar:
    """Provide trading day and session information."""

    def __init__(
        self,
        repository: ICalendarRepository,
        holiday_manager: HolidayManager,
        *,
        timezone: str = DEFAULT_TIMEZONE,
    ) -> None:
        """Initialize market calendar."""
        self._repository = repository
        self._holiday_manager = holiday_manager
        self._timezone = timezone

    def get_config(self, exchange: str) -> MarketCalendarConfig | None:
        """Return calendar configuration."""
        return self._repository.get_calendar_config(exchange)

    def is_trading_day(self, exchange: str, on_date: date) -> bool:
        """Return whether a date is a trading day."""
        return self._holiday_manager.is_trading_day(exchange, on_date)

    def get_sessions(self, exchange: str) -> list[TradingSession]:
        """Return configured sessions for an exchange."""
        return self._repository.get_sessions(exchange)

    def get_regular_session(self, exchange: str) -> TradingSession | None:
        """Return the default regular session."""
        for session in self.get_sessions(exchange):
            if session.session_type == SessionType.REGULAR:
                return session
        return None

    def market_open(self, exchange: str) -> time | None:
        """Return regular market open time."""
        session = self.get_regular_session(exchange)
        return session.start_time if session else None

    def market_close(self, exchange: str) -> time | None:
        """Return regular market close time."""
        session = self.get_regular_session(exchange)
        return session.end_time if session else None

    def pre_open_window(self, exchange: str) -> tuple[time, time] | None:
        """Return pre-open session window."""
        for session in self.get_sessions(exchange):
            if session.session_type == SessionType.PRE_OPEN:
                return session.start_time, session.end_time
        return None

    def post_close_window(self, exchange: str) -> tuple[time, time] | None:
        """Return post-close session window."""
        for session in self.get_sessions(exchange):
            if session.session_type == SessionType.POST_CLOSE:
                return session.start_time, session.end_time
        return None

    def is_market_open(self, exchange: str, moment: datetime) -> bool:
        """Return whether the market is open at a given moment."""
        if not self.is_trading_day(exchange, moment.date()):
            return False
        session = self.get_regular_session(exchange)
        if session is None:
            return False
        current = moment.time()
        return session.start_time <= current <= session.end_time

    def is_half_day(self, exchange: str, on_date: date) -> bool:
        """Return whether a date is a half trading day."""
        session = self._holiday_manager.get_special_session(exchange, on_date)
        return session is not None and session.is_half_day

    def is_special_session(self, exchange: str, on_date: date) -> bool:
        """Return whether a date has a special session."""
        return self._holiday_manager.get_special_session(exchange, on_date) is not None
