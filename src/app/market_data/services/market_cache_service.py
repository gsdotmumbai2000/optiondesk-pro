"""Market cache service facade."""

from decimal import Decimal

from app.market_data.cache.live_tick_cache import LiveTickCache
from app.market_data.cache.market_cache import MarketCache
from app.market_data.models.tick import TickSnapshot


class MarketCacheService:
    """Thread-safe market cache for live ticks and normalized quotes."""

    def __init__(
        self,
        live_cache: LiveTickCache | None = None,
        market_cache: MarketCache | None = None,
    ) -> None:
        """Initialize cache service."""
        self._live = live_cache or LiveTickCache()
        self._market = market_cache or MarketCache()

    @property
    def live(self) -> LiveTickCache:
        """Return live tick cache."""
        return self._live

    @property
    def market(self) -> MarketCache:
        """Return normalized market cache."""
        return self._market

    def put_tick(self, tick: TickSnapshot) -> None:
        """Store live tick."""
        self._live.put(tick)

    def get_tick(self, exchange: str, symbol: str, **parts: str) -> TickSnapshot | None:
        """Return cached tick."""
        return self._live.get(exchange, symbol, **parts)

    def latest_price(self, exchange: str, symbol: str, **parts: str) -> Decimal | None:
        """Return latest traded price."""
        tick = self.get_tick(exchange, symbol, **parts)
        return tick.ltp if tick is not None else None

    def snapshot_ticks(self) -> dict[str, TickSnapshot]:
        """Return all cached ticks."""
        return self._live.snapshot()

    def purge_expired(self) -> int:
        """Purge expired cache entries."""
        return self._live.purge_expired() + self._market.purge_expired()
