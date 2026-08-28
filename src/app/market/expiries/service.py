"""Expiry service."""

from datetime import date, datetime, time

from app.market.cache.market_cache import MarketCache
from app.market.enums import ExpiryType
from app.market.expiries.models import ExpiryRecord


class ExpiryService:
    """Application service for expiry operations."""

    def __init__(self, cache: MarketCache) -> None:
        """Initialize service."""
        self._cache = cache

    def nearest_expiry(
        self,
        underlying: str,
        exchange: str,
        *,
        on_date: date,
        expiry_type: ExpiryType = ExpiryType.WEEKLY,
    ) -> ExpiryRecord | None:
        """Return nearest expiry."""
        return self._cache.expiry_manager.nearest_expiry(
            underlying,
            exchange,
            on_date=on_date,
            expiry_type=expiry_type,
        )

    def list_upcoming_expiries(
        self,
        underlying: str,
        exchange: str,
        *,
        on_date: date,
        weeks_ahead: int = 8,
    ) -> list[ExpiryRecord]:
        """Return sorted, deduplicated weekly+monthly expiries ahead of on_date."""
        return self._cache.expiry_manager.list_upcoming_expiries(
            underlying, exchange, on_date=on_date, weeks_ahead=weeks_ahead
        )

    def next_expiry(
        self,
        underlying: str,
        exchange: str,
        *,
        after_date: date,
        expiry_type: ExpiryType = ExpiryType.WEEKLY,
    ) -> ExpiryRecord | None:
        """Return next expiry after a date."""
        return self._cache.expiry_manager.next_expiry(
            underlying,
            exchange,
            after_date=after_date,
            expiry_type=expiry_type,
        )

    def calculate_dte(self, exchange: str, from_date: date, expiry_date: date) -> int:
        """Calculate trading days to expiry."""
        return self._cache.expiry_manager.calculate_dte(
            exchange, from_date, expiry_date
        )

    def calculate_tte(
        self,
        exchange: str,
        now: datetime,
        expiry_date: date,
        *,
        market_close: time | None = None,
    ) -> int:
        """Calculate seconds to expiry."""
        close = market_close or time(15, 30)
        return self._cache.expiry_manager.calculate_tte(
            exchange, now, expiry_date, market_close=close
        )

    def validate_expiry(self, exchange: str, expiry_date: date) -> bool:
        """Validate an expiry date."""
        return self._cache.expiry_manager.validate_expiry(exchange, expiry_date)
