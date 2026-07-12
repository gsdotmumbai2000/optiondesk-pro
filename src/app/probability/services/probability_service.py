"""Probability application service."""

from app.events.event_bus import EventBus
from app.probability.cache.probability_cache import ProbabilityCache
from app.probability.engine.probability_engine import ProbabilityEngine
from app.probability.events import ProbabilityCalculatedEvent, ProbabilityUpdatedEvent
from app.probability.exceptions import ProbabilityException
from app.probability.models.probability_result import ProbabilityResult
from app.probability.models.request import ProbabilityAnalysisRequest
from app.probability.providers.cache_keys import build_cache_key
from app.probability.validation.probability_validator import ProbabilityValidator


class ProbabilityService:
    """Orchestrate probability analytics, caching, and events."""

    def __init__(
        self,
        engine: ProbabilityEngine,
        validator: ProbabilityValidator | None = None,
        cache: ProbabilityCache | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize service."""
        self._engine = engine
        self._validator = validator or ProbabilityValidator()
        self._cache = cache or ProbabilityCache()
        self._event_bus = event_bus

    @property
    def cache(self) -> ProbabilityCache:
        """Return probability cache."""
        return self._cache

    def calculate(self, request: ProbabilityAnalysisRequest) -> ProbabilityResult:
        """Calculate and cache probability analytics."""
        try:
            self._validator.validate(request)
            result = self._engine.calculate(request)
            key = build_cache_key(request)
            self._cache.put(key, result)
            self._publish_events(key)
            return result
        except ProbabilityException:
            raise

    def get_latest(self, request: ProbabilityAnalysisRequest) -> ProbabilityResult | None:
        """Return latest cached result."""
        return self._cache.get_latest(build_cache_key(request))

    def refresh(self, request: ProbabilityAnalysisRequest) -> ProbabilityResult:
        """Invalidate and recalculate."""
        self._cache.invalidate(build_cache_key(request))
        return self.calculate(request)

    def _publish_events(self, key: str) -> None:
        if self._event_bus is None:
            return
        payload = {"key": key}
        self._event_bus.publish(ProbabilityCalculatedEvent(payload=payload))
        self._event_bus.publish(ProbabilityUpdatedEvent(payload=payload))
