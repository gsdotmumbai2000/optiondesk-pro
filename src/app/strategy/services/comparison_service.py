"""Strategy comparison service."""

from app.events.event_bus import EventBus
from app.strategy.comparison.comparator import StrategyComparison, compare_many, rank_by_score
from app.strategy.events import StrategyComparedEvent
from app.strategy.models.evaluation import StrategyEvaluation


class StrategyComparisonService:
    """Compare and rank strategy evaluations."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize comparison service."""
        self._event_bus = event_bus

    def compare(
        self,
        evaluations: tuple[StrategyEvaluation, ...],
    ) -> StrategyComparison:
        """Compare multiple evaluations."""
        result = compare_many(evaluations)
        if self._event_bus is not None:
            self._event_bus.publish(
                StrategyComparedEvent(
                    payload={"count": len(evaluations)}
                )
            )
        return result

    def rank(
        self,
        evaluations: tuple[StrategyEvaluation, ...],
    ) -> tuple[StrategyEvaluation, ...]:
        """Rank evaluations by score."""
        return rank_by_score(evaluations)
