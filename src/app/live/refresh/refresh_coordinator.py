"""Refresh policy coordinator."""

import time
from threading import Event, RLock

from app.live.models.chain_key import ChainKey
from app.live.models.enums import RefreshMode


class RefreshCoordinator:
    """Gate live analytics refresh by configured mode."""

    _INTERVALS = {
        RefreshMode.EVERY_TICK: 0.0,
        RefreshMode.MS_250: 0.25,
        RefreshMode.MS_500: 0.5,
        RefreshMode.SEC_1: 1.0,
        RefreshMode.SEC_5: 5.0,
    }

    def __init__(self, mode: RefreshMode = RefreshMode.MS_500) -> None:
        self._mode = mode
        self._lock = RLock()
        self._last_refresh: dict[str, float] = {}
        self._manual_pending: set[str] = set()
        self._stop = Event()

    @property
    def mode(self) -> RefreshMode:
        return self._mode

    def set_mode(self, mode: RefreshMode) -> None:
        with self._lock:
            self._mode = mode

    def should_refresh(self, key: ChainKey) -> bool:
        if self._mode == RefreshMode.MANUAL:
            return key.cache_key() in self._manual_pending
        interval = self._INTERVALS.get(self._mode, 0.5)
        if interval <= 0:
            return True
        now = time.monotonic()
        cache_key = key.cache_key()
        with self._lock:
            last = self._last_refresh.get(cache_key, 0.0)
            if now - last < interval:
                return False
            self._last_refresh[cache_key] = now
            self._manual_pending.discard(cache_key)
            return True

    def request_manual_refresh(self, key: ChainKey) -> None:
        with self._lock:
            self._manual_pending.add(key.cache_key())

    def stop(self) -> None:
        self._stop.set()
