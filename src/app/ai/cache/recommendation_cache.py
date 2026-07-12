"""Thread-safe recommendation cache."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock

from app.ai.models.batch import RecommendationBatchResult
from app.ai.models.enums import AIModelVersion
from app.ai.models.result import RecommendationResult


@dataclass(frozen=True, slots=True)
class RecommendationCacheRecord:
    """Cached recommendation batch."""

    latest: RecommendationBatchResult
    previous: RecommendationBatchResult | None
    history: tuple[RecommendationBatchResult, ...]
    dismissed: tuple[str, ...]
    accepted: tuple[str, ...]
    version: AIModelVersion
    updated_at: datetime


class RecommendationCache:
    """Thread-safe cache for AI recommendations."""

    def __init__(self, *, ttl_seconds: int = 600, history_limit: int = 20) -> None:
        """Initialize cache."""
        self._ttl_seconds = ttl_seconds
        self._history_limit = history_limit
        self._lock = RLock()
        self._records: dict[str, RecommendationCacheRecord] = {}
        self._expires_at: dict[str, datetime] = {}

    def put(self, key: str, result: RecommendationBatchResult) -> None:
        """Store latest batch result."""
        with self._lock:
            existing = self._records.get(key)
            history = (existing.history if existing else ()) + (
                (existing.latest,) if existing else ()
            )
            history = history[-self._history_limit :]
            dismissed = existing.dismissed if existing else ()
            accepted = existing.accepted if existing else ()
            self._records[key] = RecommendationCacheRecord(
                latest=result,
                previous=existing.latest if existing else None,
                history=history,
                dismissed=dismissed,
                accepted=accepted,
                version=result.model_version,
                updated_at=datetime.now(timezone.utc),
            )
            self._expires_at[key] = datetime.now(timezone.utc) + timedelta(
                seconds=self._ttl_seconds
            )

    def get_latest(self, key: str) -> RecommendationBatchResult | None:
        """Return latest batch if not expired."""
        with self._lock:
            self._purge_if_expired(key)
            record = self._records.get(key)
            return record.latest if record else None

    def get_history(self, key: str) -> tuple[RecommendationBatchResult, ...]:
        """Return historical batches."""
        with self._lock:
            record = self._records.get(key)
            return record.history if record else ()

    def dismiss(self, key: str, recommendation_id: str) -> None:
        """Mark recommendation as dismissed."""
        with self._lock:
            record = self._records.get(key)
            if record is None:
                return
            dismissed = record.dismissed + (recommendation_id,)
            self._records[key] = RecommendationCacheRecord(
                latest=record.latest,
                previous=record.previous,
                history=record.history,
                dismissed=dismissed,
                accepted=record.accepted,
                version=record.version,
                updated_at=datetime.now(timezone.utc),
            )

    def accept(self, key: str, recommendation_id: str) -> None:
        """Mark recommendation as accepted."""
        with self._lock:
            record = self._records.get(key)
            if record is None:
                return
            accepted = record.accepted + (recommendation_id,)
            self._records[key] = RecommendationCacheRecord(
                latest=record.latest,
                previous=record.previous,
                history=record.history,
                dismissed=record.dismissed,
                accepted=accepted,
                version=record.version,
                updated_at=datetime.now(timezone.utc),
            )

    def invalidate(self, key: str) -> None:
        """Invalidate cache entry."""
        with self._lock:
            self._records.pop(key, None)
            self._expires_at.pop(key, None)

    def _purge_if_expired(self, key: str) -> None:
        expires = self._expires_at.get(key)
        if expires and datetime.now(timezone.utc) >= expires:
            self.invalidate(key)
