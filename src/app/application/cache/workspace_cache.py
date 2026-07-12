"""Thread-safe workspace cache."""

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Any


@dataclass(frozen=True, slots=True)
class CacheEntry:
    """Cached workspace data entry."""

    key: str
    data: Any
    cached_at: datetime


class WorkspaceCache:
    """Cache recent workspace data, reports, and strategies."""

    def __init__(self, *, limit: int = 50) -> None:
        """Initialize cache."""
        self._limit = limit
        self._lock = RLock()
        self._data: dict[str, CacheEntry] = {}
        self._reports: dict[str, CacheEntry] = {}
        self._strategies: dict[str, CacheEntry] = {}

    def put_data(self, key: str, data: Any) -> None:
        """Store recent workspace data."""
        self._put(self._data, key, data)

    def get_data(self, key: str) -> Any | None:
        """Return cached workspace data."""
        return self._get(self._data, key)

    def put_report(self, key: str, report: Any) -> None:
        """Store recent report."""
        self._put(self._reports, key, report)

    def get_report(self, key: str) -> Any | None:
        """Return cached report."""
        return self._get(self._reports, key)

    def put_strategy(self, key: str, strategy: Any) -> None:
        """Store recent strategy."""
        self._put(self._strategies, key, strategy)

    def get_strategy(self, key: str) -> Any | None:
        """Return cached strategy."""
        return self._get(self._strategies, key)

    def invalidate(self, key: str) -> None:
        """Invalidate all entries for key."""
        with self._lock:
            self._data.pop(key, None)
            self._reports.pop(key, None)
            self._strategies.pop(key, None)

    def _put(self, store: dict[str, CacheEntry], key: str, data: Any) -> None:
        with self._lock:
            store[key] = CacheEntry(key, data, datetime.now(timezone.utc))
            if len(store) > self._limit:
                oldest = min(store, key=lambda k: store[k].cached_at)
                store.pop(oldest, None)

    def _get(self, store: dict[str, CacheEntry], key: str) -> Any | None:
        with self._lock:
            entry = store.get(key)
            return entry.data if entry else None
