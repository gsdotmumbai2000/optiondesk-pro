"""Thread-safe last-tick cache with LRU and expiration."""

from datetime import datetime, timezone
from threading import RLock

from app.market_data.cache.keys import quote_key
from app.market_data.cache.lru import LruTtlCache
from app.market_data.models.tick import TickSnapshot


class LiveTickCache:
    """Maintain last tick per instrument with LRU eviction."""

    def __init__(self, *, max_entries: int = 10_000, ttl_seconds: int = 300) -> None:
        """Initialize tick cache."""
        self._store = LruTtlCache[TickSnapshot](max_entries, ttl_seconds)
        self._lock = RLock()
        self._last_update: datetime | None = None

    @property
    def last_update(self) -> datetime | None:
        """Return timestamp of the most recent tick."""
        with self._lock:
            return self._last_update

    def put(self, tick: TickSnapshot) -> None:
        """Store or replace a tick snapshot."""
        key = quote_key(
            tick.exchange,
            tick.symbol,
            expiry_date=tick.expiry_date,
            strike_price=tick.strike_price,
            option_right=tick.option_right,
        )
        with self._lock:
            self._store.put(key, tick)
            self._last_update = tick.timestamp or datetime.now(timezone.utc)

    def get(self, exchange: str, symbol: str, **parts: str) -> TickSnapshot | None:
        """Return cached tick for an instrument."""
        key = quote_key(exchange, symbol, **parts)
        with self._lock:
            return self._store.get(key)

    def snapshot(self) -> dict[str, TickSnapshot]:
        """Return shallow copy of all cached ticks."""
        with self._lock:
            return {
                key: entry.value
                for key, entry in self._store._entries.items()  # noqa: SLF001
                if entry.value is not None
            }

    def count(self) -> int:
        """Return number of cached ticks."""
        return self._store.size()

    def purge_expired(self) -> int:
        """Purge expired tick entries."""
        return self._store.purge_expired()
