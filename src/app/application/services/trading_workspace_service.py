"""Trading workspace service."""

from dataclasses import replace
from datetime import datetime, timezone

from app.ai.models.batch import RecommendationBatchResult
from app.ai.models.request import RecommendationAnalysisRequest
from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult, WorkspaceView
from app.application.ports.broker_margin_port import BrokerMarginPort
from app.application.ports.live_analytics_port import LiveAnalyticsPort
from app.application.ports.market_data_port import MarketDataPort
from app.application.registry.engine_registry import EngineRegistry
from app.application.services.broker_margin_support import BrokerMarginSupport
from app.application.services.live_analytics_support import LiveAnalyticsSupport
from app.application.services.market_data_support import MarketDataSupport
from app.application.session.session_manager import SessionManager
from app.backtesting.models.request import BacktestRequest
from app.backtesting.models.result import BacktestResult
from app.strategy.models.evaluation import StrategyEvaluation
from app.strategy.models.request import StrategyEvaluationRequest
from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.models.request import OptimizationRequest
from app.strategy_optimizer.models.result import OptimizationResult


class TradingWorkspaceService(MarketDataSupport, LiveAnalyticsSupport, BrokerMarginSupport):
    """Trading workflow orchestration API for UI."""

    def __init__(
        self,
        engines: EngineRegistry,
        sessions: SessionManager,
        cache: WorkspaceCache,
        market_data: MarketDataPort | None = None,
        live_analytics: LiveAnalyticsPort | None = None,
        broker_margin: BrokerMarginPort | None = None,
    ) -> None:
        """Initialize service."""
        MarketDataSupport.__init__(self, market_data)
        LiveAnalyticsSupport.__init__(self, live_analytics)
        BrokerMarginSupport.__init__(self, broker_margin)
        self._engines = engines
        self._sessions = sessions
        self._cache = cache

    def create_strategy(
        self,
        session_id: str,
        strategy: Strategy,
    ) -> WorkspaceOperationResult:
        """Create strategy via strategy engine."""
        created = self._engines.strategy.service.create(strategy)
        self._cache.put_strategy(created.strategy_id, created)
        self._sessions.set_active_workspace(
            session_id,
            WorkspaceType.TRADING,
            created.strategy_id,
        )
        return WorkspaceOperationResult(
            True,
            WorkspaceType.TRADING,
            "Strategy created",
            created,
        )

    def evaluate_strategy(
        self,
        session_id: str,
        request: StrategyEvaluationRequest,
    ) -> StrategyEvaluation:
        """Evaluate strategy via strategy engine."""
        result = self._engines.strategy.service.evaluate(request)
        key = f"{session_id}:{request.strategy.strategy_id}"
        self._cache.put_data(key, result)
        self._sessions.set_active_workspace(
            session_id,
            WorkspaceType.TRADING,
            request.strategy.strategy_id,
        )
        return result

    def refresh_broker_margin(
        self,
        session_id: str,
        request: StrategyEvaluationRequest,
        exchange: str = "NFO",
    ) -> StrategyEvaluation:
        """Re-evaluate the strategy with real broker margin when a broker is
        connected and supports it, falling back to the existing estimated
        margin otherwise. Intended for an explicit on-demand refresh (e.g. a
        "Refresh Margin" action) -- not the tick-driven live pipeline, since
        the underlying broker call is a rate-limited REST request."""
        broker_response = self.broker_margin(request.legs, exchange)
        if broker_response is not None:
            request = replace(request, broker_response=broker_response)
        return self.evaluate_strategy(session_id, request)

    def refresh_margin(
        self,
        session_id: str,
        exchange: str = "NFO",
    ) -> WorkspaceOperationResult:
        """Return real broker margin for the strategy currently active in
        this session's Trading workspace. Does not require a full strategy
        evaluation request -- looks up the active strategy's legs directly
        from session/cache state, the same source the live pipeline uses.

        WorkspaceOperationResult.success is False (with an explanatory
        message, not real broker data) when there's no active strategy or
        no broker margin source is available -- callers should treat that
        as "keep showing the estimated margin", not as an error."""
        session = self._sessions.get(session_id)
        strategy_id = next(
            (w.entity_id for w in session.workspaces if w.workspace == WorkspaceType.TRADING and w.entity_id),
            "",
        )
        if not strategy_id:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING, "No active strategy to refresh margin for",
            )
        strategy = self._cache.get_strategy(strategy_id)
        if strategy is None:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING, f"Strategy not found: {strategy_id}",
            )
        broker_response = self.broker_margin(strategy.legs, exchange)
        if broker_response is None:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING, "Broker margin unavailable — showing estimate",
            )
        return WorkspaceOperationResult(
            True, WorkspaceType.TRADING, "Broker margin refreshed", broker_response,
        )

    def optimize_strategy(
        self,
        session_id: str,
        request: OptimizationRequest,
    ) -> OptimizationResult:
        """Optimize strategy via optimizer engine."""
        result = self._engines.optimizer.service.optimize(request)
        self._cache.put_data(f"{session_id}:optimization", result)
        return result

    def backtest_strategy(
        self,
        session_id: str,
        request: BacktestRequest,
    ) -> BacktestResult:
        """Backtest strategy via backtesting engine."""
        result = self._engines.backtest.service.run(request)
        self._cache.put_data(f"{session_id}:backtest", result)
        return result

    def save_strategy(
        self,
        session_id: str,
        strategy: Strategy,
    ) -> WorkspaceOperationResult:
        """Save active strategy."""
        saved = self._engines.strategy.service.update(strategy)
        self._cache.put_strategy(saved.strategy_id, saved)
        return WorkspaceOperationResult(
            True,
            WorkspaceType.TRADING,
            "Strategy saved",
            saved,
        )

    def load_strategy(
        self,
        session_id: str,
        strategy_id: str,
    ) -> WorkspaceOperationResult:
        """Load strategy into trading workspace."""
        strategy = self._engines.strategy.repository.get(strategy_id)
        if strategy is None:
            return WorkspaceOperationResult(
                False,
                WorkspaceType.TRADING,
                f"Strategy not found: {strategy_id}",
            )
        self._cache.put_strategy(strategy_id, strategy)
        self._sessions.set_active_workspace(session_id, WorkspaceType.TRADING, strategy_id)
        return WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy loaded", strategy)

    def generate_recommendation(
        self,
        session_id: str,
        request: RecommendationAnalysisRequest,
    ) -> RecommendationBatchResult:
        """Generate AI recommendation."""
        result = self._engines.ai.service.generate(request)
        self._cache.put_data(f"{session_id}:recommendations", result)
        return result

    def view(self, session_id: str) -> WorkspaceView:
        """Return trading workspace view."""
        session = self._sessions.get(session_id)
        entity = next(
            (w.entity_id for w in session.workspaces if w.workspace == WorkspaceType.TRADING),
            "",
        )
        return WorkspaceView(
            workspace=WorkspaceType.TRADING,
            title="Trading Workspace",
            summary=f"Active strategy: {entity or 'none'}",
            entity_id=entity,
            updated_at=datetime.now(timezone.utc),
        )

    def live_quote(
        self,
        session_id: str,
        symbol: str,
        exchange: str = "NSE",
    ) -> WorkspaceOperationResult:
        """Return live quote for trading workspace."""
        tick = self.latest_tick(symbol, exchange)
        payload = tick.model_dump(mode="json") if tick is not None else {}
        return WorkspaceOperationResult(
            tick is not None,
            WorkspaceType.TRADING,
            f"Live quote for {symbol}",
            payload,
        )

    def live_trading_analytics(
        self,
        session_id: str,
        symbol: str,
        exchange: str = "NSE",
        expiry_date: str = "",
    ) -> WorkspaceOperationResult:
        """Return live analytics for trading decisions."""
        snapshot = self.live_analytics_snapshot(symbol, exchange, expiry_date)
        payload = {}
        if snapshot is not None:
            payload = {
                "underlying": snapshot.underlying,
                "margin": snapshot.margin is not None,
                "risk": snapshot.risk is not None,
            }
        return WorkspaceOperationResult(
            snapshot is not None,
            WorkspaceType.TRADING,
            f"Live analytics for {symbol}",
            payload,
        )
