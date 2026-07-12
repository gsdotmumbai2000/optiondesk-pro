"""Constraint service."""

from app.strategy.models.evaluation import StrategyEvaluation
from app.strategy_optimizer.constraints.checker import ConstraintChecker
from app.strategy_optimizer.models.constraints import OptimizationConstraints


class ConstraintService:
    """Apply optimization constraints."""

    def __init__(self, checker: ConstraintChecker | None = None) -> None:
        """Initialize constraint service."""
        self._checker = checker or ConstraintChecker()

    def filter(
        self,
        evaluations: tuple[StrategyEvaluation, ...],
        constraints: OptimizationConstraints,
    ) -> tuple[StrategyEvaluation, ...]:
        """Return evaluations passing constraints."""
        return tuple(
            ev for ev in evaluations if self._checker.passes(ev, constraints)
        )
