"""Thread-safe live portfolio cache."""

from threading import RLock

from app.live.models.chain_key import ChainKey
from app.market_data.cache.lru import LruTtlCache


class LivePortfolioCache:
    """Cache portfolio and position greeks."""

    def __init__(self, *, max_entries: int = 500, ttl_seconds: int = 120) -> None:
        self._store = LruTtlCache[dict[str, object]](max_entries, ttl_seconds)
        self._lock = RLock()

    def put(self, portfolio_id: str, payload: dict[str, object]) -> None:
        with self._lock:
            self._store.put(portfolio_id, payload)

    def get(self, portfolio_id: str) -> dict[str, object] | None:
        with self._lock:
            return self._store.get(portfolio_id)

    def put_position(self, key: ChainKey, greeks: dict[str, object]) -> None:
        with self._lock:
            self._store.put(f"pos:{key.cache_key()}", greeks)

    def get_position(self, key: ChainKey) -> dict[str, object] | None:
        with self._lock:
            return self._store.get(f"pos:{key.cache_key()}")

    def purge_expired(self) -> int:
        return self._store.purge_expired()
