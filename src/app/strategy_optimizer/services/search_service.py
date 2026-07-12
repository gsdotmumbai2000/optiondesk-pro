"""Search service."""

from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.models.request import OptimizationRequest
from app.strategy_optimizer.search.registry import resolve_search_algorithm


class SearchService:
    """Manage search algorithm execution."""

    def search(
        self,
        candidates: tuple[Strategy, ...],
        request: OptimizationRequest,
    ) -> tuple[Strategy, ...]:
        """Run search algorithm on candidates."""
        algorithm = resolve_search_algorithm(request.preferences.search_algorithm)
        return algorithm.search(candidates, request)
