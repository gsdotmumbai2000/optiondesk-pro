"""Payoff application service."""

from app.events.event_bus import EventBus
from app.payoff.cache.payoff_cache import PayoffCache
from app.payoff.engine.payoff_engine import PayoffEngine
from app.payoff.events import (
    BreakevenUpdatedEvent,
    PayoffCalculatedEvent,
    PayoffCurveUpdatedEvent,
    PayoffUpdatedEvent,
)
from app.payoff.exceptions import PayoffException
from app.payoff.models.request import PayoffAnalysisRequest
from app.payoff.models.result import PayoffResult
from app.payoff.providers.cache_keys import build_cache_key
from app.payoff.validation.payoff_validator import PayoffValidator


class PayoffService:
    """Orchestrate payoff analytics, caching, and events."""

    def __init__(
        self,
        engine: PayoffEngine,
        validator: PayoffValidator | None = None,
        cache: PayoffCache | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize service."""
        self._engine = engine
        self._validator = validator or PayoffValidator()
        self._cache = cache or PayoffCache()
        self._event_bus = event_bus

    @property
    def cache(self) -> PayoffCache:
        """Return payoff cache."""
        return self._cache

    @property
    def engine(self) -> PayoffEngine:
        """Return payoff engine."""
        return self._engine

    def calculate(self, request: PayoffAnalysisRequest) -> PayoffResult:
        """Calculate and cache payoff analytics."""
        try:
            self._validator.validate(request)
            result = self._engine.calculate(request)
            key = build_cache_key(request)
            self._cache.put(key, result)
            self._publish_events(key, result)
            return result
        except PayoffException:
            raise

    def get_latest(self, request: PayoffAnalysisRequest) -> PayoffResult | None:
        """Return latest cached result."""
        return self._cache.get_latest(build_cache_key(request))

    def refresh(self, request: PayoffAnalysisRequest) -> PayoffResult:
        """Invalidate and recalculate."""
        self._cache.invalidate(build_cache_key(request))
        return self.calculate(request)

    def _publish_events(self, key: str, result: PayoffResult) -> None:
        if self._event_bus is None:
            return
        payload = {"key": key}
        self._event_bus.publish(PayoffCalculatedEvent(payload=payload))
        self._event_bus.publish(PayoffUpdatedEvent(payload=payload))
        self._event_bus.publish(
            PayoffCurveUpdatedEvent(
                payload={"points": str(len(result.payoff_curve.points))}
            )
        )
        self._event_bus.publish(
            BreakevenUpdatedEvent(
                payload={"breakevens": [str(b) for b in result.breakevens]}
            )
        )
