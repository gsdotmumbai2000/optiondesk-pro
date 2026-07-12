"""Holiday service."""

from datetime import date

from app.market.cache.market_cache import MarketCache
from app.market.holidays.models import Holiday


class HolidayService:
    """Application service for holiday operations."""

    def __init__(self, cache: MarketCache) -> None:
        """Initialize service."""
        self._cache = cache

    def get_holidays(self, exchange: str) -> list[Holiday]:
        """Return holidays for an exchange."""
        return self._cache.holiday_manager.get_holidays(exchange)

    def is_trading_day(self, exchange: str, on_date: date) -> bool:
        """Return whether a date is a trading day."""
        return self._cache.holiday_manager.is_trading_day(exchange, on_date)

    def is_muhurat(self, exchange: str, on_date: date) -> bool:
        """Return whether a date has muhurat trading."""
        return self._cache.holiday_manager.is_muhurat_session(exchange, on_date)

    def next_trading_day(self, exchange: str, from_date: date) -> date:
        """Return next trading day."""
        return self._cache.holiday_manager.next_trading_day(exchange, from_date)
