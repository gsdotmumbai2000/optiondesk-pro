"""Monitoring scheduler."""

from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock

from app.monitor.models.enums import MonitoringInterval

MonitorCallback = Callable[[], None]


@dataclass(frozen=True, slots=True)
class ScheduleConfig:
    """Monitoring schedule configuration."""

    interval: MonitoringInterval
    custom_seconds: int = 0


class MonitoringScheduler:
    """Configurable monitoring interval scheduler (framework)."""

    def __init__(self) -> None:
        """Initialize scheduler."""
        self._lock = RLock()
        self._jobs: dict[str, ScheduleConfig] = {}
        self._running: set[str] = set()

    def register(
        self,
        session_id: str,
        config: ScheduleConfig,
        callback: MonitorCallback,
    ) -> None:
        """Register monitoring job (stores config; execution delegated)."""
        with self._lock:
            self._jobs[session_id] = config
            self._running.add(session_id)

    def stop(self, session_id: str) -> None:
        """Stop monitoring session."""
        with self._lock:
            self._running.discard(session_id)
            self._jobs.pop(session_id, None)

    def is_running(self, session_id: str) -> bool:
        """Return whether session is active."""
        with self._lock:
            return session_id in self._running

    def interval_seconds(self, config: ScheduleConfig) -> int:
        """Resolve interval to seconds."""
        mapping = {
            MonitoringInterval.REAL_TIME: 0,
            MonitoringInterval.EVERY_TICK: 0,
            MonitoringInterval.EVERY_SECOND: 1,
            MonitoringInterval.EVERY_MINUTE: 60,
            MonitoringInterval.CUSTOM: config.custom_seconds,
        }
        return mapping.get(config.interval, 60)

    def active_sessions(self) -> tuple[str, ...]:
        """Return active session ids."""
        with self._lock:
            return tuple(self._running)
