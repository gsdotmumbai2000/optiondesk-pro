"""Thread-safe live greeks cache."""

from threading import RLock

from app.greeks.models.greeks_result import GreeksResult
from app.live.models.chain_key import ChainKey
from app.market_data.cache.lru import LruTtlCache


class LiveGreeksCache:
    """Cache greeks results keyed by chain."""

    def __init__(self, *, max_entries: int = 2_000, ttl_seconds: int = 120) -> None:
        self._store = LruTtlCache[GreeksResult](max_entries, ttl_seconds)
        self._lock = RLock()

    def put(self, key: ChainKey, result: GreeksResult) -> None:
        with self._lock:
            self._store.put(key.cache_key(), result)

    def get(self, key: ChainKey) -> GreeksResult | None:
        with self._lock:
            return self._store.get(key.cache_key())

    def purge_expired(self) -> int:
        return self._store.purge_expired()
