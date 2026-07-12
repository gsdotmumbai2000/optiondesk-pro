"""Market calendar service."""

from datetime import date, datetime, time

from app.market.cache.market_cache import MarketCache


class MarketCalendarService:
    """Application service for market calendar operations."""

    def __init__(self, cache: MarketCache) -> None:
        """Initialize service."""
        self._cache = cache

    def is_trading_day(self, exchange: str, on_date: date) -> bool:
        """Return whether a date is a trading day."""
        return self._cache.market_calendar.is_trading_day(exchange, on_date)

    def is_market_open(self, exchange: str, moment: datetime) -> bool:
        """Return whether the market is open."""
        return self._cache.market_calendar.is_market_open(exchange, moment)

    def market_open(self, exchange: str) -> time | None:
        """Return market open time."""
        return self._cache.market_calendar.market_open(exchange)

    def market_close(self, exchange: str) -> time | None:
        """Return market close time."""
        return self._cache.market_calendar.market_close(exchange)

    def pre_open_window(self, exchange: str) -> tuple[time, time] | None:
        """Return pre-open window."""
        return self._cache.market_calendar.pre_open_window(exchange)

    def post_close_window(self, exchange: str) -> tuple[time, time] | None:
        """Return post-close window."""
        return self._cache.market_calendar.post_close_window(exchange)

    def is_half_day(self, exchange: str, on_date: date) -> bool:
        """Return whether date is a half trading day."""
        return self._cache.market_calendar.is_half_day(exchange, on_date)
