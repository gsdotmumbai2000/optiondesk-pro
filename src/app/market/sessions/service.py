"""Trading session service."""

from app.market.cache.market_cache import MarketCache
from app.market.sessions.models import TradingSession


class TradingSessionService:
    """Application service for trading session operations."""

    def __init__(self, cache: MarketCache) -> None:
        """Initialize service."""
        self._cache = cache

    def get_sessions(self, exchange: str) -> list[TradingSession]:
        """Return trading sessions for an exchange."""
        return self._cache.market_calendar.get_sessions(exchange)

    def get_regular_session(self, exchange: str) -> TradingSession | None:
        """Return the regular trading session."""
        return self._cache.market_calendar.get_regular_session(exchange)
