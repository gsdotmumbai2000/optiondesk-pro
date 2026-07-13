"""Tick throughput statistics."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock


@dataclass
class TickStatistics:
    """Track live tick throughput."""

    total_ticks: int = 0
    dropped_ticks: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _lock: RLock = field(default_factory=RLock, repr=False)

    def record_tick(self) -> None:
        """Increment tick counter."""
        with self._lock:
            self.total_ticks += 1

    def record_drop(self) -> None:
        """Increment dropped tick counter."""
        with self._lock:
            self.dropped_ticks += 1

    def ticks_per_second(self) -> float:
        """Return average ticks per second since start."""
        with self._lock:
            elapsed = (datetime.now(timezone.utc) - self.started_at).total_seconds()
            if elapsed <= 0:
                return 0.0
            return self.total_ticks / elapsed
