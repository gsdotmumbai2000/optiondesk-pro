"""Strategy optimizer bootstrap."""

from app.events.event_bus import EventBus
from app.strategy.bootstrap import StrategyProvider
from app.strategy.services.evaluation_service import StrategyEvaluationService
from app.strategy_optimizer.cache.optimization_cache import OptimizationCache
from app.strategy_optimizer.engine.optimizer_engine import OptimizerEngine
from app.strategy_optimizer.services.constraint_service import ConstraintService
from app.strategy_optimizer.services.evaluation_adapter import EvaluationServiceAdapter
from app.strategy_optimizer.services.objective_service import ObjectiveService
from app.strategy_optimizer.services.ranking_service import RankingService
from app.strategy_optimizer.services.search_service import SearchService
from app.strategy_optimizer.services.strategy_optimizer import StrategyOptimizer
from app.strategy_optimizer.validation.optimizer_validator import OptimizerValidator


class OptimizerProvider:
    """Wire strategy optimizer dependencies."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize provider."""
        strategy_provider = StrategyProvider(event_bus)
        evaluation_service = StrategyEvaluationService(strategy_provider.engine)
        evaluator = EvaluationServiceAdapter(evaluation_service)
        self.engine = OptimizerEngine(evaluator)
        self.validator = OptimizerValidator()
        self.cache = OptimizationCache()
        self.search_service = SearchService(evaluator)
        self.ranking_service = RankingService()
        self.constraint_service = ConstraintService()
        self.objective_service = ObjectiveService()
        self.service = StrategyOptimizer(
            self.engine,
            self.validator,
            self.cache,
            event_bus,
        )
