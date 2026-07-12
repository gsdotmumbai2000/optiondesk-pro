"""Margin advisor."""

from decimal import Decimal

from app.ai.models.context import EngineContextSnapshot
from app.ai.models.request import RecommendationAnalysisRequest


class MarginAdvisor:
    """Margin advisory notes from engine outputs."""

    def advise(
        self,
        request: RecommendationAnalysisRequest,
        context: EngineContextSnapshot,
    ) -> tuple[str, ...]:
        """Return margin advisory notes."""
        notes: list[str] = []
        if context.margin_utilization > Decimal("0.75"):
            notes.append(f"Margin utilization at {context.margin_utilization:.0%}")
        if context.available_margin < context.portfolio_value * Decimal("0.1"):
            notes.append("Low available margin relative to portfolio value")
        return tuple(notes)
