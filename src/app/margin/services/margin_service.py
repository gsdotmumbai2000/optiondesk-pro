"""Margin application service."""

from app.events.event_bus import EventBus
from app.margin.cache.margin_cache import MarginCache
from app.margin.engine.margin_engine import MarginEngine
from app.margin.events import (
    BuyingPowerUpdatedEvent,
    MarginCalculatedEvent,
    MarginOptimizationCompletedEvent,
    MarginUpdatedEvent,
)
from app.margin.exceptions import MarginException
from app.margin.models.optimization import MarginOptimizationResult
from app.margin.models.request import MarginAnalysisRequest
from app.margin.models.result import MarginResult
from app.margin.optimization.margin_optimizer import MarginOptimizer
from app.margin.providers.cache_keys import build_cache_key
from app.margin.services.capital_efficiency_service import CapitalEfficiencyService
from app.margin.validation.margin_validator import MarginValidator


class MarginService:
    """Orchestrate margin analytics, caching, and events."""

    def __init__(
        self,
        engine: MarginEngine,
        validator: MarginValidator | None = None,
        cache: MarginCache | None = None,
        event_bus: EventBus | None = None,
        optimizer: MarginOptimizer | None = None,
    ) -> None:
        """Initialize service."""
        self._engine = engine
        self._validator = validator or MarginValidator()
        self._cache = cache or MarginCache()
        self._event_bus = event_bus
        self._optimizer = optimizer or MarginOptimizer()
        self._capital_efficiency = CapitalEfficiencyService(self._optimizer)

    @property
    def cache(self) -> MarginCache:
        """Return margin cache."""
        return self._cache

    @property
    def capital_efficiency_service(self) -> CapitalEfficiencyService:
        """Return capital efficiency service."""
        return self._capital_efficiency

    def calculate(self, request: MarginAnalysisRequest) -> MarginResult:
        """Calculate and cache margin analytics."""
        try:
            self._validator.validate(request)
            result = self._engine.calculate(request)
            key = build_cache_key(request)
            self._cache.put(key, result, broker_response=request.broker_response)
            self._publish_margin_events(key, result)
            return result
        except MarginException:
            raise

    def optimize(
        self,
        request: MarginAnalysisRequest,
        result: MarginResult | None = None,
    ) -> MarginOptimizationResult:
        """Run margin optimization on calculated result."""
        if result is None:
            result = self.calculate(request)
        opt = self._optimizer.optimize(request, result)
        if self._event_bus is not None:
            self._event_bus.publish(
                MarginOptimizationCompletedEvent(
                    payload={"score": str(opt.capital_efficiency_score)}
                )
            )
        return opt

    def estimate(self, request: MarginAnalysisRequest):
        """Estimate margin without full analytics."""
        self._validator.validate(request)
        return self._engine.estimate(request)

    def get_latest(self, request: MarginAnalysisRequest) -> MarginResult | None:
        """Return latest cached result."""
        return self._cache.get_latest(build_cache_key(request))

    def refresh(self, request: MarginAnalysisRequest) -> MarginResult:
        """Invalidate and recalculate."""
        self._cache.invalidate(build_cache_key(request))
        return self.calculate(request)

    def _publish_margin_events(self, key: str, result: MarginResult) -> None:
        if self._event_bus is None:
            return
        payload = {"key": key}
        self._event_bus.publish(MarginCalculatedEvent(payload=payload))
        self._event_bus.publish(MarginUpdatedEvent(payload=payload))
        self._event_bus.publish(
            BuyingPowerUpdatedEvent(
                payload={"buying_power": str(result.buying_power)}
            )
        )
