"""Market advisor."""

from app.ai.models.context import EngineContextSnapshot
from app.ai.models.request import RecommendationAnalysisRequest


class MarketAdvisor:
    """Market advisory notes from engine outputs."""

    def advise(
        self,
        request: RecommendationAnalysisRequest,
        context: EngineContextSnapshot,
    ) -> tuple[str, ...]:
        """Return market advisory notes."""
        notes: list[str] = []
        snap = request.market_snapshot
        if snap:
            notes.append(f"Market snapshot {snap.snapshot_id} at {snap.captured_at}")
        chain = request.option_chain_analysis
        if chain is not None:
            notes.append("Option chain analysis available from chain engine")
        vol = request.volatility_result
        if vol is not None:
            notes.append("Volatility result available from volatility engine")
        return tuple(notes)
