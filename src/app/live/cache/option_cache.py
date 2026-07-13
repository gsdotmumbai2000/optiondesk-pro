"""Thread-safe live option chain cache."""

from threading import RLock

from app.live.models.chain_key import ChainKey
from app.live.models.option_chain import LiveOptionChain
from app.market_data.cache.lru import LruTtlCache


class LiveOptionCache:
    """Cache live option chains with LRU eviction."""

    def __init__(self, *, max_entries: int = 1_000, ttl_seconds: int = 300) -> None:
        self._store = LruTtlCache[LiveOptionChain](max_entries, ttl_seconds)
        self._lock = RLock()

    def put(self, key: ChainKey, chain: LiveOptionChain) -> None:
        with self._lock:
            self._store.put(key.cache_key(), chain)

    def get(self, key: ChainKey) -> LiveOptionChain | None:
        with self._lock:
            return self._store.get(key.cache_key())

    def purge_expired(self) -> int:
        return self._store.purge_expired()
