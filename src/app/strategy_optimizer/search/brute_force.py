"""Brute force search implementation."""

from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.models.request import OptimizationRequest
from app.strategy_optimizer.search.port import SearchAlgorithm


class BruteForceSearch:
    """Evaluate all candidates (brute force)."""

    @property
    def algorithm_id(self) -> str:
        """Return algorithm identifier."""
        return "brute_force"

    def search(
        self,
        candidates: tuple[Strategy, ...],
        request: OptimizationRequest,
    ) -> tuple[Strategy, ...]:
        """Return all candidates up to max limit."""
        limit = request.preferences.max_candidates
        return candidates[:limit]
