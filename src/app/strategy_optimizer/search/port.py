"""Search algorithm interfaces."""

from typing import Protocol

from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.models.request import OptimizationRequest
from app.strategy_optimizer.search.fitness import CandidateFitnessEvaluator


class SearchAlgorithm(Protocol):
    """Search algorithm contract."""

    @property
    def algorithm_id(self) -> str:
        """Return algorithm identifier."""
        ...

    def search(
        self,
        candidates: tuple[Strategy, ...],
        request: OptimizationRequest,
        fitness: CandidateFitnessEvaluator,
    ) -> tuple[Strategy, ...]:
        """Return search space subset. `fitness` gives real per-candidate
        engine-evaluated scores, for algorithms that need feedback to guide
        their search (e.g. Simulated Annealing) rather than just slicing
        the given candidate list."""
        ...
