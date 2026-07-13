"""AI workspace service."""

from datetime import datetime, timezone

from app.ai.models.batch import RecommendationBatchResult
from app.ai.models.request import RecommendationAnalysisRequest
from app.ai.models.result import RecommendationResult
from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult, WorkspaceView
from app.application.ports.market_data_port import MarketDataPort
from app.application.registry.engine_registry import EngineRegistry
from app.application.services.market_data_support import MarketDataSupport
from app.application.session.session_manager import SessionManager


class AIWorkspaceService(MarketDataSupport):
    """AI recommendation workspace API for UI."""

    def __init__(
        self,
        engines: EngineRegistry,
        sessions: SessionManager,
        cache: WorkspaceCache,
        market_data: MarketDataPort | None = None,
    ) -> None:
        """Initialize service."""
        super().__init__(market_data)
        self._engines = engines
        self._sessions = sessions
        self._cache = cache

    def generate_recommendation(
        self,
        session_id: str,
        request: RecommendationAnalysisRequest,
    ) -> RecommendationBatchResult:
        """Generate AI recommendations."""
        result = self._engines.ai.service.generate(request)
        self._cache.put_data(f"{session_id}:ai", result)
        return result

    def explain_recommendation(
        self,
        recommendation: RecommendationResult,
    ) -> WorkspaceOperationResult:
        """Return explanation for recommendation."""
        explanation = recommendation.detailed_explanation
        return WorkspaceOperationResult(
            True,
            WorkspaceType.AI,
            "Explanation ready",
            explanation,
        )

    def compare_recommendations(
        self,
        recommendations: tuple[RecommendationResult, ...],
    ) -> WorkspaceOperationResult:
        """Compare multiple recommendations."""
        ranked = sorted(
            recommendations,
            key=lambda r: r.scores.priority_score,
            reverse=True,
        )
        return WorkspaceOperationResult(
            True,
            WorkspaceType.AI,
            f"Compared {len(ranked)} recommendations",
            ranked,
        )

    def recommendation_history(self, session_id: str) -> WorkspaceOperationResult:
        """Return recommendation history from memory."""
        state = self._engines.ai.memory.state()
        return WorkspaceOperationResult(
            True,
            WorkspaceType.AI,
            f"{len(state.history)} historical recommendations",
            state,
        )

    def accept(self, session_id: str, request: RecommendationAnalysisRequest, rec_id: str) -> None:
        """Accept recommendation."""
        self._engines.ai.service.accept(request, rec_id)

    def dismiss(self, session_id: str, request: RecommendationAnalysisRequest, rec_id: str) -> None:
        """Dismiss recommendation."""
        self._engines.ai.service.dismiss(request, rec_id)

    def view(self, session_id: str) -> WorkspaceView:
        """Return AI workspace view."""
        memory = self._engines.ai.memory.state()
        return WorkspaceView(
            workspace=WorkspaceType.AI,
            title="AI Workspace",
            summary=f"{len(memory.recent)} recent recommendations",
            entity_id="",
            updated_at=datetime.now(timezone.utc),
        )

    def market_context_price(
        self,
        session_id: str,
        symbol: str,
        exchange: str = "NSE",
    ) -> WorkspaceOperationResult:
        """Return live price for AI recommendation context."""
        price = self.latest_price(symbol, exchange)
        return WorkspaceOperationResult(
            price is not None,
            WorkspaceType.AI,
            f"Context price for {symbol}",
            {"symbol": symbol, "exchange": exchange, "price": str(price or "")},
        )
