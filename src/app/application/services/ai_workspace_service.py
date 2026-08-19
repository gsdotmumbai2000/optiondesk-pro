"""AI workspace service."""

from datetime import datetime, timezone
from decimal import Decimal

from app.ai.models.batch import RecommendationBatchResult
from app.ai.models.request import RecommendationAnalysisRequest
from app.ai.models.result import RecommendationResult
from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult, WorkspaceView
from app.application.ports.live_analytics_port import LiveAnalyticsPort
from app.application.ports.market_data_port import MarketDataPort
from app.application.registry.engine_registry import EngineRegistry
from app.application.services.live_analytics_support import LiveAnalyticsSupport
from app.application.services.market_data_support import MarketDataSupport
from app.application.session.session_manager import SessionManager
from app.portfolio.models.request import PortfolioAnalysisRequest


class AIWorkspaceService(MarketDataSupport, LiveAnalyticsSupport):
    """AI recommendation workspace API for UI."""

    def __init__(
        self,
        engines: EngineRegistry,
        sessions: SessionManager,
        cache: WorkspaceCache,
        market_data: MarketDataPort | None = None,
        live_analytics: LiveAnalyticsPort | None = None,
    ) -> None:
        """Initialize service."""
        MarketDataSupport.__init__(self, market_data)
        LiveAnalyticsSupport.__init__(self, live_analytics)
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

    def generate_recommendation_for_active_strategy(
        self,
        session_id: str,
        exchange: str = "NFO",
    ) -> WorkspaceOperationResult:
        """Generate AI recommendations for the strategy currently active in
        this session's Trading workspace, building a real
        RecommendationAnalysisRequest from:
        - portfolio_result: always real -- this session's portfolio,
          created fresh (empty, zero cash) if none exists yet, the same
          lazy-creation pattern paper trading's account uses. It's the
          only required field on the request; everything below is
          individually optional there, so this degrades gracefully rather
          than blocking on any one piece being unavailable.
        - risk/margin/probability/chain-analysis/volatility results and a
          market snapshot: from the active strategy's live analytics, when
          its chain has been subscribed. Reads the cached snapshot from the
          last "Evaluate" (does not force a fresh recompute -- this action
          is "what does the AI think of the current state", not itself an
          evaluation trigger).
        - optimization_result: the cached result from the last "Optimize"
          run this session, if any.

        WorkspaceOperationResult.success is False (no batch data) when
        there's no active strategy -- callers should keep showing whatever
        recommendations were last generated, not treat this as an error."""
        session = self._sessions.get(session_id)
        strategy_id = next(
            (w.entity_id for w in session.workspaces if w.workspace == WorkspaceType.TRADING and w.entity_id),
            "",
        )
        if not strategy_id:
            return WorkspaceOperationResult(
                False, WorkspaceType.AI, "No active strategy to generate recommendations for",
            )
        strategy = self._cache.get_strategy(strategy_id)
        if strategy is None:
            return WorkspaceOperationResult(
                False, WorkspaceType.AI, f"Strategy not found: {strategy_id}",
            )

        portfolio_id = self._resolve_or_create_portfolio(session_id)
        portfolio_result = self._engines.portfolio.service.calculate(
            PortfolioAnalysisRequest(portfolio_id=portfolio_id)
        )

        risk_result = margin_result = probability_result = None
        option_chain_analysis = volatility_result = market_snapshot = None
        leg = strategy.legs[0] if strategy.legs else None
        if leg is not None and leg.underlying and leg.expiry:
            leg_exchange = leg.exchange or exchange
            expiry_date = leg.expiry.strftime("%d-%b-%Y")
            snapshot = self.live_analytics_snapshot(leg.underlying, leg_exchange, expiry_date)
            if snapshot is not None:
                risk_result = snapshot.risk
                margin_result = snapshot.margin
                probability_result = snapshot.probability
                option_chain_analysis = snapshot.chain_analysis
                volatility_result = snapshot.volatility
            context = self.evaluation_context(leg.underlying, leg_exchange, expiry_date)
            if context is not None:
                market_snapshot = context.market_snapshot

        optimization_result = self._cache.get_data(f"{session_id}:optimization")

        request = RecommendationAnalysisRequest(
            session_id=session_id,
            portfolio_result=portfolio_result,
            risk_result=risk_result,
            margin_result=margin_result,
            probability_result=probability_result,
            strategy_evaluation=None,
            optimization_result=optimization_result,
            position_monitor_result=None,
            market_snapshot=market_snapshot,
            option_chain_analysis=option_chain_analysis,
            volatility_result=volatility_result,
        )
        batch = self.generate_recommendation(session_id, request)
        return WorkspaceOperationResult(
            True, WorkspaceType.AI,
            f"{len(batch.recommendations)} recommendation(s) generated",
            batch,
        )

    def _resolve_or_create_portfolio(self, session_id: str) -> str:
        """Return this session's active portfolio id, creating a fresh
        (empty, zero-cash) portfolio if none is active yet or the one on
        record no longer exists in the repository."""
        session = self._sessions.get(session_id)
        portfolio_id = next(
            (w.entity_id for w in session.workspaces if w.workspace == WorkspaceType.PORTFOLIO and w.entity_id),
            "",
        )
        if portfolio_id and self._engines.portfolio.repository.get(portfolio_id) is not None:
            return portfolio_id
        portfolio = self._engines.portfolio.service.create_portfolio(
            f"AI Recommendations — {session_id}", Decimal("0"),
        )
        self._sessions.set_active_workspace(session_id, WorkspaceType.PORTFOLIO, portfolio.portfolio_id)
        return portfolio.portfolio_id

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

    def live_recommendation_context(
        self,
        session_id: str,
        symbol: str,
        exchange: str = "NSE",
        expiry_date: str = "",
    ) -> WorkspaceOperationResult:
        """Return live analytics context for AI recommendations."""
        snapshot = self.live_analytics_snapshot(symbol, exchange, expiry_date)
        payload = {}
        if snapshot is not None:
            payload = {
                "underlying": snapshot.underlying,
                "has_chain_analysis": snapshot.chain_analysis is not None,
                "has_probability": snapshot.probability is not None,
            }
        return WorkspaceOperationResult(
            snapshot is not None,
            WorkspaceType.AI,
            f"AI context for {symbol}",
            payload,
        )
