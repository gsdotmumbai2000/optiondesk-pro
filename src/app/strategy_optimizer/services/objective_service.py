"""Objective service."""

from decimal import Decimal

from app.strategy.models.evaluation import StrategyEvaluation
from app.strategy_optimizer.models.preferences import OptimizationPreferences
from app.strategy_optimizer.objectives.weighter import ObjectiveWeighter


class ObjectiveService:
    """Apply optimization objectives."""

    def __init__(self, weighter: ObjectiveWeighter | None = None) -> None:
        """Initialize objective service."""
        self._weighter = weighter or ObjectiveWeighter()

    def score(
        self,
        evaluation: StrategyEvaluation,
        preferences: OptimizationPreferences,
    ) -> Decimal:
        """Return objective-weighted score."""
        return self._weighter.weight(evaluation, preferences)
