"""Thread-safe monitor cache."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock

from app.monitor.models.alert import Alert
from app.monitor.models.enums import MonitorModelVersion
from app.monitor.models.result import MonitorResult


@dataclass(frozen=True, slots=True)
class MonitorCacheRecord:
    """Cached monitor result."""

    latest: MonitorResult
    previous: MonitorResult | None
    history: tuple[MonitorResult, ...]
    acknowledged: tuple[Alert, ...]
    version: MonitorModelVersion
    updated_at: datetime


class MonitorCache:
    """Thread-safe cache for monitor results and alerts."""

    def __init__(self, *, ttl_seconds: int = 300, history_limit: int = 50) -> None:
        """Initialize cache."""
        self._ttl_seconds = ttl_seconds
        self._history_limit = history_limit
        self._lock = RLock()
        self._records: dict[str, MonitorCacheRecord] = {}
        self._expires_at: dict[str, datetime] = {}
        self._acknowledged: dict[str, list[Alert]] = {}

    def put(self, key: str, result: MonitorResult) -> None:
        """Store latest monitor result."""
        with self._lock:
            existing = self._records.get(key)
            history = (existing.history if existing else ()) + (
                (existing.latest,) if existing else ()
            )
            history = history[-self._history_limit :]
            ack = tuple(self._acknowledged.get(key, ()))
            self._records[key] = MonitorCacheRecord(
                latest=result,
                previous=existing.latest if existing else None,
                history=history,
                acknowledged=ack,
                version=result.model_version,
                updated_at=datetime.now(timezone.utc),
            )
            self._expires_at[key] = datetime.now(timezone.utc) + timedelta(
                seconds=self._ttl_seconds
            )

    def get_latest(self, key: str) -> MonitorResult | None:
        """Return latest result if not expired."""
        with self._lock:
            self._purge_if_expired(key)
            record = self._records.get(key)
            return record.latest if record else None

    def get_history(self, key: str) -> tuple[MonitorResult, ...]:
        """Return historical results."""
        with self._lock:
            record = self._records.get(key)
            return record.history if record else ()

    def acknowledge(self, key: str, alert: Alert) -> None:
        """Store acknowledged alert."""
        with self._lock:
            bucket = self._acknowledged.setdefault(key, [])
            bucket.append(alert)
            record = self._records.get(key)
            if record:
                self._records[key] = MonitorCacheRecord(
                    latest=record.latest,
                    previous=record.previous,
                    history=record.history,
                    acknowledged=tuple(bucket),
                    version=record.version,
                    updated_at=datetime.now(timezone.utc),
                )

    def get_acknowledged(self, key: str) -> tuple[Alert, ...]:
        """Return acknowledged alerts."""
        with self._lock:
            record = self._records.get(key)
            return record.acknowledged if record else ()

    def invalidate(self, key: str) -> None:
        """Invalidate cache entry."""
        with self._lock:
            self._records.pop(key, None)
            self._expires_at.pop(key, None)
            self._acknowledged.pop(key, None)

    def _purge_if_expired(self, key: str) -> None:
        expires = self._expires_at.get(key)
        if expires and datetime.now(timezone.utc) >= expires:
            self.invalidate(key)
