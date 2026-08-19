"""Search service."""

from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.engine.ports import EvaluationPort
from app.strategy_optimizer.models.request import OptimizationRequest
from app.strategy_optimizer.search.fitness import CandidateFitnessEvaluator
from app.strategy_optimizer.search.registry import resolve_search_algorithm


class SearchService:
    """Manage search algorithm execution."""

    def __init__(self, evaluator: EvaluationPort) -> None:
        """Initialize service."""
        self._evaluator = evaluator

    def search(
        self,
        candidates: tuple[Strategy, ...],
        request: OptimizationRequest,
    ) -> tuple[Strategy, ...]:
        """Run search algorithm on candidates."""
        algorithm = resolve_search_algorithm(request.preferences.search_algorithm)
        fitness = CandidateFitnessEvaluator(self._evaluator, request)
        return algorithm.search(candidates, request, fitness)
