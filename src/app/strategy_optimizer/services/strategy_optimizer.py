"""Strategy optimizer application service."""

from app.events.event_bus import EventBus
from app.strategy_optimizer.cache.optimization_cache import OptimizationCache
from app.strategy_optimizer.engine.optimizer_engine import OptimizerEngine
from app.strategy_optimizer.events import (
    OptimizationCompletedEvent,
    OptimizationStartedEvent,
    RecommendationGeneratedEvent,
)
from app.strategy_optimizer.exceptions import OptimizerException
from app.strategy_optimizer.models.request import OptimizationRequest
from app.strategy_optimizer.models.result import OptimizationResult
from app.strategy_optimizer.providers.cache_keys import build_cache_key
from app.strategy_optimizer.validation.optimizer_validator import OptimizerValidator


class StrategyOptimizer:
    """Orchestrate strategy optimization, caching, and events."""

    def __init__(
        self,
        engine: OptimizerEngine,
        validator: OptimizerValidator | None = None,
        cache: OptimizationCache | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize optimizer service."""
        self._engine = engine
        self._validator = validator or OptimizerValidator()
        self._cache = cache or OptimizationCache()
        self._event_bus = event_bus

    @property
    def cache(self) -> OptimizationCache:
        """Return optimization cache."""
        return self._cache

    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        """Run optimization and cache results."""
        try:
            self._validator.validate(request)
            if self._event_bus is not None:
                self._event_bus.publish(OptimizationStartedEvent(payload={}))
            result = self._engine.optimize(request)
            key = build_cache_key(request)
            self._cache.put(key, result)
            self._publish_completed(key, result)
            return result
        except OptimizerException:
            raise

    def get_latest(self, request: OptimizationRequest) -> OptimizationResult | None:
        """Return latest cached result."""
        return self._cache.get_latest(build_cache_key(request))

    def _publish_completed(self, key: str, result: OptimizationResult) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            OptimizationCompletedEvent(payload={"key": key, "count": len(result.candidate_strategies)})
        )
        self._event_bus.publish(
            RecommendationGeneratedEvent(
                payload={"recommendation": result.recommendation}
            )
        )
