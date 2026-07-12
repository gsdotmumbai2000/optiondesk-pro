"""Search algorithm interfaces."""

from typing import Protocol

from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.models.request import OptimizationRequest


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
    ) -> tuple[Strategy, ...]:
        """Return search space subset."""
        ...
