"""Thread-safe optimization cache."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock

from app.strategy_optimizer.models.enums import OptimizerModelVersion
from app.strategy_optimizer.models.result import OptimizationResult


@dataclass(frozen=True, slots=True)
class OptimizationCacheRecord:
    """Cached optimization result."""

    latest: OptimizationResult
    previous: OptimizationResult | None
    history: tuple[OptimizationResult, ...]
    version: OptimizerModelVersion
    updated_at: datetime


class OptimizationCache:
    """Thread-safe cache for optimization results."""

    def __init__(self, *, ttl_seconds: int = 600, history_limit: int = 20) -> None:
        """Initialize cache."""
        self._ttl_seconds = ttl_seconds
        self._history_limit = history_limit
        self._lock = RLock()
        self._records: dict[str, OptimizationCacheRecord] = {}
        self._saved: dict[str, OptimizationResult] = {}
        self._expires_at: dict[str, datetime] = {}

    def put(self, key: str, result: OptimizationResult) -> None:
        """Store latest optimization result."""
        with self._lock:
            existing = self._records.get(key)
            history = (existing.history if existing else ()) + (
                (existing.latest,) if existing else ()
            )
            history = history[-self._history_limit :]
            self._records[key] = OptimizationCacheRecord(
                latest=result,
                previous=existing.latest if existing else None,
                history=history,
                version=result.model_version,
                updated_at=datetime.now(timezone.utc),
            )
            self._expires_at[key] = datetime.now(timezone.utc) + timedelta(
                seconds=self._ttl_seconds
            )

    def get_latest(self, key: str) -> OptimizationResult | None:
        """Return latest result if not expired."""
        with self._lock:
            self._purge_if_expired(key)
            record = self._records.get(key)
            return record.latest if record else None

    def get_history(self, key: str) -> tuple[OptimizationResult, ...]:
        """Return historical results."""
        with self._lock:
            record = self._records.get(key)
            return record.history if record else ()

    def save(self, name: str, result: OptimizationResult) -> None:
        """Save named optimization result."""
        with self._lock:
            self._saved[name] = result

    def get_saved(self, name: str) -> OptimizationResult | None:
        """Return saved result by name."""
        with self._lock:
            return self._saved.get(name)

    def invalidate(self, key: str) -> None:
        """Invalidate cache entry."""
        with self._lock:
            self._records.pop(key, None)
            self._expires_at.pop(key, None)

    def _purge_if_expired(self, key: str) -> None:
        expires = self._expires_at.get(key)
        if expires and datetime.now(timezone.utc) >= expires:
            self.invalidate(key)
