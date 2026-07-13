"""Synchronize live analytics subscribers."""

from collections.abc import Callable
from threading import RLock

from app.live.models.chain_key import ChainKey


class SynchronizationService:
    """Track and notify live analytics subscribers."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._subscribers: dict[str, list[Callable[[ChainKey], None]]] = {}

    def subscribe(self, key: ChainKey, callback: Callable[[ChainKey], None]) -> None:
        with self._lock:
            listeners = self._subscribers.setdefault(key.cache_key(), [])
            listeners.append(callback)

    def unsubscribe(self, key: ChainKey, callback: Callable[[ChainKey], None]) -> None:
        with self._lock:
            listeners = self._subscribers.get(key.cache_key(), [])
            if callback in listeners:
                listeners.remove(callback)

    def notify(self, key: ChainKey) -> None:
        with self._lock:
            listeners = list(self._subscribers.get(key.cache_key(), []))
        for callback in listeners:
            callback(key)

    def subscriber_count(self, key: ChainKey) -> int:
        with self._lock:
            return len(self._subscribers.get(key.cache_key(), []))
