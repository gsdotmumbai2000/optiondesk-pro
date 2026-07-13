"""Thread-safe live risk cache."""

from threading import RLock

from app.live.models.analytics import LiveAnalyticsSnapshot
from app.live.models.chain_key import ChainKey
from app.market_data.cache.lru import LruTtlCache


class LiveRiskCache:
    """Cache risk and margin analytics."""

    def __init__(self, *, max_entries: int = 1_000, ttl_seconds: int = 120) -> None:
        self._store = LruTtlCache[LiveAnalyticsSnapshot](max_entries, ttl_seconds)
        self._lock = RLock()

    def put(self, key: ChainKey, snapshot: LiveAnalyticsSnapshot) -> None:
        with self._lock:
            self._store.put(key.cache_key(), snapshot)

    def get(self, key: ChainKey) -> LiveAnalyticsSnapshot | None:
        with self._lock:
            return self._store.get(key.cache_key())

    def purge_expired(self) -> int:
        return self._store.purge_expired()
