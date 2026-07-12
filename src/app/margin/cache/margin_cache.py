"""Thread-safe margin cache."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock

from app.margin.models.broker_response import BrokerMarginResponse
from app.margin.models.enums import MarginModelVersion
from app.margin.models.result import MarginResult


@dataclass(frozen=True, slots=True)
class MarginCacheRecord:
    """Cached margin result."""

    latest: MarginResult
    previous: MarginResult | None
    history: tuple[MarginResult, ...]
    broker_response: BrokerMarginResponse | None
    version: MarginModelVersion
    updated_at: datetime


class MarginCache:
    """Thread-safe cache for margin analytics."""

    def __init__(self, *, ttl_seconds: int = 300, history_limit: int = 20) -> None:
        """Initialize cache."""
        self._ttl_seconds = ttl_seconds
        self._history_limit = history_limit
        self._lock = RLock()
        self._records: dict[str, MarginCacheRecord] = {}
        self._expires_at: dict[str, datetime] = {}

    def put(
        self,
        key: str,
        result: MarginResult,
        *,
        broker_response: BrokerMarginResponse | None = None,
    ) -> None:
        """Store latest margin result."""
        with self._lock:
            existing = self._records.get(key)
            history = (existing.history if existing else ()) + (
                (existing.latest,) if existing else ()
            )
            history = history[-self._history_limit :]
            self._records[key] = MarginCacheRecord(
                latest=result,
                previous=existing.latest if existing else None,
                history=history,
                broker_response=broker_response,
                version=result.model_version,
                updated_at=datetime.now(timezone.utc),
            )
            self._expires_at[key] = datetime.now(timezone.utc) + timedelta(
                seconds=self._ttl_seconds
            )

    def get_latest(self, key: str) -> MarginResult | None:
        """Return latest result if not expired."""
        with self._lock:
            self._purge_if_expired(key)
            record = self._records.get(key)
            return record.latest if record else None

    def get_history(self, key: str) -> tuple[MarginResult, ...]:
        """Return historical results."""
        with self._lock:
            record = self._records.get(key)
            return record.history if record else ()

    def get_broker_response(self, key: str) -> BrokerMarginResponse | None:
        """Return cached broker response."""
        with self._lock:
            record = self._records.get(key)
            return record.broker_response if record else None

    def invalidate(self, key: str) -> None:
        """Invalidate cache entry."""
        with self._lock:
            self._records.pop(key, None)
            self._expires_at.pop(key, None)

    def _purge_if_expired(self, key: str) -> None:
        expires = self._expires_at.get(key)
        if expires and datetime.now(timezone.utc) >= expires:
            self.invalidate(key)
