"""Calendar repository."""

from datetime import time
from pathlib import Path

from app.logging.logging_manager import get_logger
from app.market.calendar.models import MarketCalendarConfig
from app.market.enums import ExchangeCode, SessionType
from app.market.repositories.data_loader import MarketDataLoader
from app.market.sessions.models import TradingSession

logger = get_logger(__name__)

DEFAULT_SESSIONS = [
    TradingSession(
        exchange=ExchangeCode.NSEFO.value,
        session_type=SessionType.PRE_OPEN,
        session_name="Pre Open",
        start_time=time(9, 0),
        end_time=time(9, 8),
    ),
    TradingSession(
        exchange=ExchangeCode.NSEFO.value,
        session_type=SessionType.REGULAR,
        session_name="Regular",
        start_time=time(9, 15),
        end_time=time(15, 30),
        is_default=True,
    ),
    TradingSession(
        exchange=ExchangeCode.NSEFO.value,
        session_type=SessionType.POST_CLOSE,
        session_name="Post Close",
        start_time=time(15, 40),
        end_time=time(16, 0),
    ),
]


class CalendarRepository:
    """In-memory calendar and session repository."""

    def __init__(self, seed_directory: Path | None = None) -> None:
        """Initialize repository."""
        self._seed_directory = seed_directory
        self._configs: dict[str, MarketCalendarConfig] = {}
        self._sessions: list[TradingSession] = []

    def initialize(self) -> None:
        """Load calendar configuration and sessions."""
        self._configs = {
            exchange.value: MarketCalendarConfig(exchange=exchange.value)
            for exchange in ExchangeCode
        }
        self._sessions = list(DEFAULT_SESSIONS)
        self._load_seed_files()
        logger.info(
            "Calendar repository loaded {count} sessions", count=len(self._sessions)
        )

    def close(self) -> None:
        """Clear repository data."""
        self._configs.clear()
        self._sessions.clear()

    def get_calendar_config(self, exchange: str) -> MarketCalendarConfig | None:
        """Return calendar config for exchange."""
        return self._configs.get(exchange.upper())

    def get_sessions(self, exchange: str) -> list[TradingSession]:
        """Return sessions for exchange."""
        code = exchange.upper()
        return [item for item in self._sessions if item.exchange.upper() == code]

    def save_session(self, session: TradingSession) -> None:
        """Save a trading session."""
        self._sessions.append(session)

    def _load_seed_files(self) -> None:
        """Load sessions from seed files."""
        if self._seed_directory is None:
            return
        loader = MarketDataLoader()
        for path in sorted(self._seed_directory.glob("sessions.*")):
            for record in loader.load_records(path):
                self._sessions.append(TradingSession.model_validate(record))
