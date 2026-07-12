"""Portfolio advisor."""

from app.ai.models.context import EngineContextSnapshot
from app.ai.models.request import RecommendationAnalysisRequest


class PortfolioAdvisor:
    """Portfolio-level advisory notes from engine outputs."""

    def advise(
        self,
        request: RecommendationAnalysisRequest,
        context: EngineContextSnapshot,
    ) -> tuple[str, ...]:
        """Return portfolio advisory notes."""
        notes: list[str] = []
        if context.unrealized_pnl < 0:
            notes.append(f"Portfolio unrealized loss: {context.unrealized_pnl}")
        if context.cash_balance < context.portfolio_value * 0.1:
            notes.append("Cash reserves below 10% of portfolio value")
        if context.open_position_count > 50:
            notes.append(f"High position count: {context.open_position_count}")
        return tuple(notes)
