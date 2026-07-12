"""Strategy advisor."""

from decimal import Decimal

from app.ai.models.context import EngineContextSnapshot
from app.ai.models.request import RecommendationAnalysisRequest


class StrategyAdvisor:
    """Strategy advisory notes from engine outputs."""

    def advise(
        self,
        request: RecommendationAnalysisRequest,
        context: EngineContextSnapshot,
    ) -> tuple[str, ...]:
        """Return strategy advisory notes."""
        notes: list[str] = []
        ev = request.strategy_evaluation
        if ev is None:
            return ()
        notes.append(f"Strategy: {ev.strategy.name}")
        if ev.analysis.probability_of_profit < Decimal("0.5"):
            notes.append(
                f"Low POP: {ev.analysis.probability_of_profit:.0%} from strategy engine"
            )
        return tuple(notes)
