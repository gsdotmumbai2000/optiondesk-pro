"""Volatility application service."""

from app.events.event_bus import EventBus
from app.volatility.cache.volatility_cache import VolatilityCache
from app.volatility.engine.volatility_engine import VolatilityEngine
from app.volatility.events import VolatilityCalculatedEvent, VolatilityUpdatedEvent
from app.volatility.exceptions import VolatilityException
from app.volatility.models.request import VolatilityAnalysisRequest
from app.volatility.models.volatility_result import VolatilityResult
from app.volatility.providers.cache_keys import build_cache_key
from app.volatility.validation.volatility_validator import VolatilityValidator


class VolatilityService:
    """Orchestrate volatility analytics, caching, and events."""

    def __init__(
        self,
        engine: VolatilityEngine,
        validator: VolatilityValidator | None = None,
        cache: VolatilityCache | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize service."""
        self._engine = engine
        self._validator = validator or VolatilityValidator()
        self._cache = cache or VolatilityCache()
        self._event_bus = event_bus

    @property
    def cache(self) -> VolatilityCache:
        """Return volatility cache."""
        return self._cache

    def calculate(self, request: VolatilityAnalysisRequest) -> VolatilityResult:
        """Calculate and cache volatility analytics."""
        try:
            self._validator.validate(request)
            result = self._engine.calculate(request)
            key = build_cache_key(request)
            self._cache.put(key, result)
            self._publish_events(key)
            return result
        except VolatilityException:
            raise

    def get_latest(self, request: VolatilityAnalysisRequest) -> VolatilityResult | None:
        """Return latest cached result."""
        return self._cache.get_latest(build_cache_key(request))

    def refresh(self, request: VolatilityAnalysisRequest) -> VolatilityResult:
        """Invalidate and recalculate."""
        self._cache.invalidate(build_cache_key(request))
        return self.calculate(request)

    def _publish_events(self, key: str) -> None:
        if self._event_bus is None:
            return
        payload = {"key": key}
        self._event_bus.publish(VolatilityCalculatedEvent(payload=payload))
        self._event_bus.publish(VolatilityUpdatedEvent(payload=payload))
