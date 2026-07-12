"""Thread-safe option chain cache."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock

from app.option_chain.models.analysis import OptionChainAnalysis
from app.option_chain.models.enums import OptionChainModelVersion


@dataclass(frozen=True, slots=True)
class OptionChainCacheRecord:
    """Cached option chain result."""

    latest: OptionChainAnalysis
    previous: OptionChainAnalysis | None
    history: tuple[OptionChainAnalysis, ...]
    version: OptionChainModelVersion
    updated_at: datetime


class OptionChainCache:
    """Thread-safe cache for option chain analytics."""

    def __init__(self, *, ttl_seconds: int = 300, history_limit: int = 20) -> None:
        """Initialize cache."""
        self._ttl_seconds = ttl_seconds
        self._history_limit = history_limit
        self._lock = RLock()
        self._records: dict[str, OptionChainCacheRecord] = {}
        self._expires_at: dict[str, datetime] = {}

    def put(self, key: str, result: OptionChainAnalysis) -> None:
        """Store latest option chain result."""
        with self._lock:
            existing = self._records.get(key)
            history = (existing.history if existing else ()) + (
                (existing.latest,) if existing else ()
            )
            history = history[-self._history_limit :]
            self._records[key] = OptionChainCacheRecord(
                latest=result,
                previous=existing.latest if existing else None,
                history=history,
                version=result.model_version,
                updated_at=datetime.now(timezone.utc),
            )
            self._expires_at[key] = datetime.now(timezone.utc) + timedelta(
                seconds=self._ttl_seconds
            )

    def get_latest(self, key: str) -> OptionChainAnalysis | None:
        """Return latest result if not expired."""
        with self._lock:
            self._purge_if_expired(key)
            record = self._records.get(key)
            return record.latest if record else None

    def invalidate(self, key: str) -> None:
        """Invalidate cache entry."""
        with self._lock:
            self._records.pop(key, None)
            self._expires_at.pop(key, None)

    def _purge_if_expired(self, key: str) -> None:
        expires = self._expires_at.get(key)
        if expires and datetime.now(timezone.utc) >= expires:
            self.invalidate(key)
