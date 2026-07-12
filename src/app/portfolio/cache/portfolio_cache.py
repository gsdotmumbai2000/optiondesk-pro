"""Thread-safe portfolio cache."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from threading import RLock

from app.portfolio.models.enums import PortfolioModelVersion
from app.portfolio.models.portfolio import PortfolioSnapshot
from app.portfolio.models.result import PortfolioResult


@dataclass(frozen=True, slots=True)
class PortfolioCacheRecord:
    """Cached portfolio analytics."""

    latest: PortfolioResult
    previous: PortfolioResult | None
    history: tuple[PortfolioResult, ...]
    snapshots: tuple[PortfolioSnapshot, ...]
    value_history: tuple[Decimal, ...]
    version: PortfolioModelVersion
    updated_at: datetime


class PortfolioCache:
    """Thread-safe cache for portfolio results and snapshots."""

    def __init__(self, *, ttl_seconds: int = 3600, history_limit: int = 100) -> None:
        """Initialize cache."""
        self._ttl_seconds = ttl_seconds
        self._history_limit = history_limit
        self._lock = RLock()
        self._records: dict[str, PortfolioCacheRecord] = {}
        self._expires_at: dict[str, datetime] = {}

    def put(
        self,
        key: str,
        result: PortfolioResult,
        snapshot: PortfolioSnapshot | None = None,
    ) -> None:
        """Store latest portfolio result."""
        with self._lock:
            existing = self._records.get(key)
            history = (existing.history if existing else ()) + (
                (existing.latest,) if existing else ()
            )
            history = history[-self._history_limit :]
            snapshots = existing.snapshots if existing else ()
            if snapshot is not None:
                snapshots = snapshots + (snapshot,)
                snapshots = snapshots[-self._history_limit :]
            values = (existing.value_history if existing else ()) + (
                result.portfolio_value,
            )
            values = values[-self._history_limit :]
            self._records[key] = PortfolioCacheRecord(
                latest=result,
                previous=existing.latest if existing else None,
                history=history,
                snapshots=snapshots,
                value_history=values,
                version=result.model_version,
                updated_at=datetime.now(timezone.utc),
            )
            self._expires_at[key] = datetime.now(timezone.utc) + timedelta(
                seconds=self._ttl_seconds
            )

    def get_latest(self, key: str) -> PortfolioResult | None:
        """Return latest result if not expired."""
        with self._lock:
            self._purge_if_expired(key)
            record = self._records.get(key)
            return record.latest if record else None

    def get_history(self, key: str) -> tuple[PortfolioResult, ...]:
        """Return historical results."""
        with self._lock:
            record = self._records.get(key)
            return record.history if record else ()

    def get_snapshots(self, key: str) -> tuple[PortfolioSnapshot, ...]:
        """Return stored snapshots."""
        with self._lock:
            record = self._records.get(key)
            return record.snapshots if record else ()

    def get_value_history(self, key: str) -> tuple[Decimal, ...]:
        """Return portfolio value history."""
        with self._lock:
            record = self._records.get(key)
            return record.value_history if record else ()

    def invalidate(self, key: str) -> None:
        """Invalidate cache entry."""
        with self._lock:
            self._records.pop(key, None)
            self._expires_at.pop(key, None)

    def _purge_if_expired(self, key: str) -> None:
        expires = self._expires_at.get(key)
        if expires and datetime.now(timezone.utc) >= expires:
            self.invalidate(key)
