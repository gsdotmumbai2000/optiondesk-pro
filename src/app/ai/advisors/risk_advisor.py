"""Risk advisor."""

from decimal import Decimal

from app.ai.models.context import EngineContextSnapshot
from app.ai.models.request import RecommendationAnalysisRequest


class RiskAdvisor:
    """Risk advisory notes from engine outputs."""

    def advise(
        self,
        request: RecommendationAnalysisRequest,
        context: EngineContextSnapshot,
    ) -> tuple[str, ...]:
        """Return risk advisory notes."""
        notes: list[str] = []
        if context.risk_score > Decimal("60"):
            notes.append(f"Elevated risk score: {context.risk_score}")
        if abs(context.net_delta) > Decimal("50"):
            notes.append(f"Directional delta exposure: {context.net_delta}")
        if request.risk_result and request.risk_result.limit_warnings:
            count = len(request.risk_result.limit_warnings)
            notes.append(f"{count} risk limit warnings from risk engine")
        return tuple(notes)
