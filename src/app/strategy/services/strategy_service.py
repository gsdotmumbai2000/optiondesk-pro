"""Strategy application service."""

from app.events.event_bus import EventBus
from app.strategy.builders.strategy_builder import StrategyBuilder
from app.strategy.cache.strategy_cache import StrategyCache
from app.strategy.engine.strategy_engine import StrategyEngine
from app.strategy.events import (
    StrategyCreatedEvent,
    StrategyDeletedEvent,
    StrategyEvaluatedEvent,
    StrategyModifiedEvent,
)
from app.strategy.exceptions import StrategyException
from app.strategy.models.evaluation import StrategyEvaluation
from app.strategy.models.request import StrategyEvaluationRequest
from app.strategy.models.strategy import Strategy
from app.strategy.providers.cache_keys import build_cache_key
from app.strategy.repository.strategy_repository import StrategyRepository
from app.strategy.services.comparison_service import StrategyComparisonService
from app.strategy.services.evaluation_service import StrategyEvaluationService
from app.strategy.services.recognition_service import StrategyRecognitionService
from app.strategy.services.template_service import StrategyTemplateService
from app.strategy.validation.strategy_validator import StrategyValidator


class StrategyService:
    """Orchestrate strategy lifecycle, evaluation, and events."""

    def __init__(
        self,
        engine: StrategyEngine,
        validator: StrategyValidator | None = None,
        cache: StrategyCache | None = None,
        repository: StrategyRepository | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize strategy service."""
        self._engine = engine
        self._validator = validator or StrategyValidator()
        self._cache = cache or StrategyCache()
        self._repository = repository or StrategyRepository()
        self._event_bus = event_bus
        self._evaluation = StrategyEvaluationService(engine, self._validator)
        self._recognition = StrategyRecognitionService()
        self._comparison = StrategyComparisonService(event_bus)
        self._templates = StrategyTemplateService(self._cache)

    @property
    def cache(self) -> StrategyCache:
        """Return strategy cache."""
        return self._cache

    @property
    def repository(self) -> StrategyRepository:
        """Return strategy repository."""
        return self._repository

    @property
    def builder(self) -> StrategyBuilder:
        """Return new strategy builder."""
        return StrategyBuilder()

    @property
    def recognition_service(self) -> StrategyRecognitionService:
        """Return recognition service."""
        return self._recognition

    @property
    def comparison_service(self) -> StrategyComparisonService:
        """Return comparison service."""
        return self._comparison

    @property
    def template_service(self) -> StrategyTemplateService:
        """Return template service."""
        return self._templates

    def create(self, strategy: Strategy) -> Strategy:
        """Create and persist strategy."""
        try:
            self._validator.validate_strategy(strategy)
            self._repository.save(strategy)
            self._publish(StrategyCreatedEvent, strategy.strategy_id)
            return strategy
        except StrategyException:
            raise

    def update(self, strategy: Strategy) -> Strategy:
        """Update persisted strategy."""
        self._validator.validate_strategy(strategy)
        self._repository.save(strategy)
        self._publish(StrategyModifiedEvent, strategy.strategy_id)
        return strategy

    def delete(self, strategy_id: str) -> bool:
        """Delete strategy by id."""
        deleted = self._repository.delete(strategy_id)
        if deleted:
            self._publish(StrategyDeletedEvent, strategy_id)
        return deleted

    def evaluate(self, request: StrategyEvaluationRequest) -> StrategyEvaluation:
        """Evaluate strategy via engine orchestration."""
        evaluation = self._evaluation.evaluate(request)
        key = build_cache_key(request)
        self._cache.put(key, evaluation)
        self._publish(StrategyEvaluatedEvent, request.strategy.strategy_id)
        return evaluation

    def evaluate_batch(
        self,
        requests: tuple[StrategyEvaluationRequest, ...],
    ) -> tuple[StrategyEvaluation, ...]:
        """Batch evaluate strategies."""
        return self._evaluation.evaluate_batch(requests)

    def get_latest(self, request: StrategyEvaluationRequest) -> StrategyEvaluation | None:
        """Return latest cached evaluation."""
        return self._cache.get_latest(build_cache_key(request))

    def _publish(self, event_cls, strategy_id: str) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(event_cls(payload={"strategy_id": strategy_id}))
