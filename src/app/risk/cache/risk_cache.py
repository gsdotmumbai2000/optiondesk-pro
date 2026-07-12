"""Thread-safe risk cache."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock

from app.risk.models.enums import RiskModelVersion
from app.risk.models.result import RiskResult
from app.risk.models.scenario import RiskScenarioResult
from app.risk.models.stress import StressTestResult


@dataclass(frozen=True, slots=True)
class RiskCacheRecord:
    """Cached risk result."""

    latest: RiskResult
    previous: RiskResult | None
    history: tuple[RiskResult, ...]
    stress_results: tuple[StressTestResult, ...]
    scenario_results: tuple[RiskScenarioResult, ...]
    version: RiskModelVersion
    updated_at: datetime


class RiskCache:
    """Thread-safe cache for risk analytics."""

    def __init__(self, *, ttl_seconds: int = 300, history_limit: int = 20) -> None:
        """Initialize cache."""
        self._ttl_seconds = ttl_seconds
        self._history_limit = history_limit
        self._lock = RLock()
        self._records: dict[str, RiskCacheRecord] = {}
        self._expires_at: dict[str, datetime] = {}

    def put(
        self,
        key: str,
        result: RiskResult,
        *,
        stress_results: tuple[StressTestResult, ...] = (),
        scenario_results: tuple[RiskScenarioResult, ...] = (),
    ) -> None:
        """Store latest risk result."""
        with self._lock:
            existing = self._records.get(key)
            history = (existing.history if existing else ()) + (
                (existing.latest,) if existing else ()
            )
            history = history[-self._history_limit :]
            self._records[key] = RiskCacheRecord(
                latest=result,
                previous=existing.latest if existing else None,
                history=history,
                stress_results=stress_results or result.stress_results,
                scenario_results=scenario_results,
                version=result.model_version,
                updated_at=datetime.now(timezone.utc),
            )
            self._expires_at[key] = datetime.now(timezone.utc) + timedelta(
                seconds=self._ttl_seconds
            )

    def get_latest(self, key: str) -> RiskResult | None:
        """Return latest result if not expired."""
        with self._lock:
            self._purge_if_expired(key)
            record = self._records.get(key)
            return record.latest if record else None

    def get_history(self, key: str) -> tuple[RiskResult, ...]:
        """Return historical results."""
        with self._lock:
            record = self._records.get(key)
            return record.history if record else ()

    def get_stress_results(self, key: str) -> tuple[StressTestResult, ...]:
        """Return cached stress results."""
        with self._lock:
            record = self._records.get(key)
            return record.stress_results if record else ()

    def invalidate(self, key: str) -> None:
        """Invalidate cache entry."""
        with self._lock:
            self._records.pop(key, None)
            self._expires_at.pop(key, None)

    def _purge_if_expired(self, key: str) -> None:
        expires = self._expires_at.get(key)
        if expires and datetime.now(timezone.utc) >= expires:
            self.invalidate(key)
