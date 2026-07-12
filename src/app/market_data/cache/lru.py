"""LRU cache with TTL support."""

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class _CacheEntry(Generic[T]):
    """Internal cache entry with expiry."""

    value: T
    expires_at: datetime | None


class LruTtlCache(Generic[T]):
    """Thread-safe LRU cache with optional TTL."""

    def __init__(self, max_size: int = 10_000, ttl_seconds: int | None = 300) -> None:
        """Initialize cache."""
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._entries: OrderedDict[str, _CacheEntry[T]] = OrderedDict()
        self._lock = RLock()

    def get(self, key: str) -> T | None:
        """Return cached value if present and not expired."""
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if entry.expires_at and datetime.now(timezone.utc) >= entry.expires_at:
                del self._entries[key]
                return None
            self._entries.move_to_end(key)
            return entry.value

    def put(self, key: str, value: T) -> None:
        """Store a value in cache."""
        with self._lock:
            expires_at = None
            if self._ttl_seconds is not None:
                expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=self._ttl_seconds
                )
            self._entries[key] = _CacheEntry(value=value, expires_at=expires_at)
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_size:
                self._entries.popitem(last=False)

    def invalidate(self, key: str) -> None:
        """Remove a cache entry."""
        with self._lock:
            self._entries.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._entries.clear()

    def purge_expired(self) -> int:
        """Remove expired entries and return count removed."""
        now = datetime.now(timezone.utc)
        removed = 0
        with self._lock:
            expired = [
                key
                for key, entry in self._entries.items()
                if entry.expires_at and now >= entry.expires_at
            ]
            for key in expired:
                del self._entries[key]
                removed += 1
        return removed

    def size(self) -> int:
        """Return current cache size."""
        with self._lock:
            return len(self._entries)
