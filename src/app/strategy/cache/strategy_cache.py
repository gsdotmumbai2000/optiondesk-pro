"""Thread-safe strategy cache."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock

from app.strategy.models.enums import StrategyModelVersion
from app.strategy.models.evaluation import StrategyEvaluation
from app.strategy.models.template import StrategyTemplate


@dataclass(frozen=True, slots=True)
class StrategyCacheRecord:
    """Cached strategy evaluation."""

    latest: StrategyEvaluation
    previous: StrategyEvaluation | None
    history: tuple[StrategyEvaluation, ...]
    version: StrategyModelVersion
    updated_at: datetime


class StrategyCache:
    """Thread-safe cache for strategy evaluations."""

    def __init__(self, *, ttl_seconds: int = 300, history_limit: int = 50) -> None:
        """Initialize cache."""
        self._ttl_seconds = ttl_seconds
        self._history_limit = history_limit
        self._lock = RLock()
        self._records: dict[str, StrategyCacheRecord] = {}
        self._favorites: set[str] = set()
        self._templates: dict[str, StrategyTemplate] = {}
        self._expires_at: dict[str, datetime] = {}

    def put(self, key: str, evaluation: StrategyEvaluation) -> None:
        """Store latest evaluation."""
        with self._lock:
            existing = self._records.get(key)
            history = (existing.history if existing else ()) + (
                (existing.latest,) if existing else ()
            )
            history = history[-self._history_limit :]
            self._records[key] = StrategyCacheRecord(
                latest=evaluation,
                previous=existing.latest if existing else None,
                history=history,
                version=evaluation.model_version,
                updated_at=datetime.now(timezone.utc),
            )
            self._expires_at[key] = datetime.now(timezone.utc) + timedelta(
                seconds=self._ttl_seconds
            )

    def get_latest(self, key: str) -> StrategyEvaluation | None:
        """Return latest evaluation if not expired."""
        with self._lock:
            self._purge_if_expired(key)
            record = self._records.get(key)
            return record.latest if record else None

    def get_history(self, key: str) -> tuple[StrategyEvaluation, ...]:
        """Return evaluation history."""
        with self._lock:
            record = self._records.get(key)
            return record.history if record else ()

    def add_favorite(self, strategy_id: str) -> None:
        """Add strategy to favorites."""
        with self._lock:
            self._favorites.add(strategy_id)

    def get_favorites(self) -> frozenset[str]:
        """Return favorite strategy ids."""
        with self._lock:
            return frozenset(self._favorites)

    def put_template(self, template: StrategyTemplate) -> None:
        """Store custom template."""
        with self._lock:
            self._templates[template.template_id] = template

    def get_template(self, template_id: str) -> StrategyTemplate | None:
        """Return template by id."""
        with self._lock:
            return self._templates.get(template_id)

    def list_templates(self) -> tuple[StrategyTemplate, ...]:
        """Return all cached templates."""
        with self._lock:
            return tuple(self._templates.values())

    def invalidate(self, key: str) -> None:
        """Invalidate cache entry."""
        with self._lock:
            self._records.pop(key, None)
            self._expires_at.pop(key, None)

    def _purge_if_expired(self, key: str) -> None:
        expires = self._expires_at.get(key)
        if expires and datetime.now(timezone.utc) >= expires:
            self.invalidate(key)
