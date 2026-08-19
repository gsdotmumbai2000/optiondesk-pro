"""Trading workspace service."""

from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal

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
from app.backtesting.models.enums import OrderSide
from app.backtesting.models.request import BacktestRequest
from app.backtesting.models.result import BacktestResult
from app.market.enums import InstrumentType
from app.paper_trading.models.account import PaperAccountSnapshot
from app.paper_trading.models.request import PaperOrderRequest
from app.strategy.models.evaluation import StrategyEvaluation
from app.strategy.models.request import StrategyEvaluationRequest
from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.models.constraints import OptimizationConstraints
from app.strategy_optimizer.models.enums import (
    MarketOutlook,
    OptimizationObjective,
    RiskPreference,
    SearchAlgorithmType,
)
from app.strategy_optimizer.models.preferences import OptimizationPreferences
from app.strategy_optimizer.models.request import OptimizationRequest
from app.strategy_optimizer.models.result import OptimizationResult

_DEFAULT_OPTIMIZATION_CAPITAL = Decimal("1000000")


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

    def list_underlyings(self) -> WorkspaceOperationResult:
        """List known underlyings (index instruments) for the strategy leg
        builder -- pure Instrument Master lookup, no broker call."""
        instruments = self._engines.market_master.instrument_service.find_by_instrument_type(
            InstrumentType.INDEX
        )
        underlyings = sorted({instrument.underlying for instrument in instruments})
        return WorkspaceOperationResult(
            True, WorkspaceType.TRADING, f"{len(underlyings)} underlyings", underlyings,
        )

    def leg_builder_context(
        self,
        underlying: str,
        exchange: str = "NFO",
    ) -> WorkspaceOperationResult:
        """Return expiry choices and lot size for a leg being added to a new
        strategy -- pure Instrument/Expiry Master lookups, no broker call.

        WorkspaceOperationResult.success is False (no data) when the
        underlying isn't in the Instrument Master or has no resolvable
        expiry."""
        instrument_service = self._engines.market_master.instrument_service
        try:
            lot_size = instrument_service.get_lot_size(underlying)
        except LookupError:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING, f"Unknown underlying: {underlying}",
            )
        today = date.today()
        weekly = instrument_service.weekly_expiry(underlying, exchange, on_date=today)
        monthly = instrument_service.monthly_expiry(underlying, exchange, on_date=today)
        expiries: list[tuple[str, date]] = []
        if weekly is not None:
            expiries.append((f"Weekly {weekly.expiry_date.isoformat()}", weekly.expiry_date))
        if monthly is not None and (weekly is None or monthly.expiry_date != weekly.expiry_date):
            expiries.append((f"Monthly {monthly.expiry_date.isoformat()}", monthly.expiry_date))
        if not expiries:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING, f"No expiry available for {underlying}",
            )
        return WorkspaceOperationResult(
            True, WorkspaceType.TRADING, "Expiry options resolved",
            {"expiries": expiries, "lot_size": lot_size},
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

    def evaluate_active_strategy(
        self,
        session_id: str,
        exchange: str = "NFO",
    ) -> WorkspaceOperationResult:
        """Evaluate the strategy currently active in this session's Trading
        workspace: synchronously refreshes live analytics (payoff, Greeks,
        risk, margin) for its chain, taken from its first leg's underlying/
        exchange/expiry (all legs of one strategy share the same chain).

        Deliberately synchronous, not the tick-driven LiveCalculationPipeline:
        this is an explicit on-demand "Evaluate" action, the same pattern as
        refresh_margin() above, so it needs the result immediately rather
        than racing the background dispatcher.

        WorkspaceOperationResult.success is False (no snapshot data) when
        there's no active strategy, the strategy has no legs, its legs are
        missing underlying/expiry, or its chain hasn't been subscribed yet
        (e.g. Market workspace hasn't loaded this underlying/expiry this
        session) -- callers should keep showing whatever was last evaluated,
        not treat this as an error."""
        session = self._sessions.get(session_id)
        strategy_id = next(
            (w.entity_id for w in session.workspaces if w.workspace == WorkspaceType.TRADING and w.entity_id),
            "",
        )
        if not strategy_id:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING, "No active strategy to evaluate",
            )
        strategy = self._cache.get_strategy(strategy_id)
        if strategy is None:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING, f"Strategy not found: {strategy_id}",
            )
        if not strategy.legs:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING, "Strategy has no legs to evaluate",
            )
        leg = strategy.legs[0]
        if not leg.underlying or not leg.expiry:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING, "Strategy legs are missing underlying/expiry",
            )
        snapshot = self.refresh_live_analytics(
            leg.underlying, leg.exchange or exchange, leg.expiry.strftime("%d-%b-%Y"),
        )
        if snapshot is None:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING,
                "Live chain unavailable — subscribe to this underlying/expiry in Market workspace first",
            )
        return WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy evaluated", snapshot)

    def optimize_strategy(
        self,
        session_id: str,
        request: OptimizationRequest,
    ) -> OptimizationResult:
        """Optimize strategy via optimizer engine."""
        result = self._engines.optimizer.service.optimize(request)
        self._cache.put_data(f"{session_id}:optimization", result)
        return result

    def optimize_active_strategy(
        self,
        session_id: str,
        exchange: str = "NFO",
    ) -> WorkspaceOperationResult:
        """Search for better variants of the strategy currently active in
        this session's Trading workspace, over the same chain
        evaluate_active_strategy() uses (its first leg's underlying/
        exchange/expiry).

        OptimizationPreferences/OptimizationConstraints use fixed defaults
        (capital, ranking size, Simulated Annealing search) since no UI
        exists yet for configuring them -- the same "sensible fixed
        defaults, no config screen" scope already used for
        run_active_strategy_backtest()'s SimulationParameters.
        primary_objective=MAX_POP is the one default that's actually
        consumed downstream: CandidateFitnessEvaluator's Simulated
        Annealing walk reads it via ObjectiveWeighter.

        WorkspaceOperationResult.success is False (no result data) when
        there's no active strategy, its legs are missing an underlying/
        expiry, or its chain hasn't been subscribed yet -- callers should
        keep showing whatever was last optimized, not treat this as an
        error."""
        session = self._sessions.get(session_id)
        strategy_id = next(
            (w.entity_id for w in session.workspaces if w.workspace == WorkspaceType.TRADING and w.entity_id),
            "",
        )
        if not strategy_id:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING, "No active strategy to optimize",
            )
        strategy = self._cache.get_strategy(strategy_id)
        if strategy is None:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING, f"Strategy not found: {strategy_id}",
            )
        if not strategy.legs:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING, "Strategy has no legs to optimize",
            )
        leg = strategy.legs[0]
        if not leg.underlying or not leg.expiry:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING, "Strategy legs are missing underlying/expiry",
            )
        underlying = leg.underlying
        leg_exchange = leg.exchange or exchange
        expiry_date = leg.expiry.strftime("%d-%b-%Y")

        context = self.evaluation_context(underlying, leg_exchange, expiry_date)
        if context is None:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING,
                "Live chain unavailable — subscribe to this underlying/expiry in Market workspace first",
            )
        snapshot = self.refresh_live_analytics(underlying, leg_exchange, expiry_date)
        if snapshot is None or snapshot.risk is None or snapshot.margin is None:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING,
                "Live analytics unavailable for this strategy — evaluate it first",
            )

        request = OptimizationRequest(
            calculation_context=context.calculation_context,
            strategy_context=None,
            market_snapshot=context.market_snapshot,
            option_chain_analysis=snapshot.chain_analysis,
            volatility_result=snapshot.volatility,
            probability_result=snapshot.probability,
            risk_result=snapshot.risk,
            margin_result=snapshot.margin,
            preferences=OptimizationPreferences(
                underlying=underlying,
                expiry=expiry_date,
                capital=_DEFAULT_OPTIMIZATION_CAPITAL,
                market_outlook=MarketOutlook.NEUTRAL,
                risk_preference=RiskPreference.MODERATE,
                primary_objective=OptimizationObjective.MAX_POP,
                search_algorithm=SearchAlgorithmType.SIMULATED_ANNEALING,
            ),
            constraints=OptimizationConstraints(),
            option_contract=context.option_contract,
            option_chain=context.option_chain,
            chain_market_snapshot=context.chain_market_snapshot,
            volatility_market_snapshot=context.volatility_market_snapshot,
            historical_data=context.historical_data,
        )
        result = self.optimize_strategy(session_id, request)
        return WorkspaceOperationResult(True, WorkspaceType.TRADING, "Optimization complete", result)

    def paper_trade_active_strategy(
        self,
        session_id: str,
        exchange: str = "NFO",
    ) -> WorkspaceOperationResult:
        """Submit every leg of the strategy currently active in this
        session's Trading workspace as a paper order -- a simulated fill
        against this session's virtual paper account (no broker routing,
        no capital at risk), using each leg's own recorded premium as the
        reference price. Unlike evaluate/optimize above, this needs no
        live chain subscription: the leg already carries the price the
        strategy was built around.

        WorkspaceOperationResult.success is False (no trades/snapshot data)
        when there's no active strategy or it has no legs -- callers should
        keep showing whatever paper account state was last shown, not
        treat this as an error."""
        session = self._sessions.get(session_id)
        strategy_id = next(
            (w.entity_id for w in session.workspaces if w.workspace == WorkspaceType.TRADING and w.entity_id),
            "",
        )
        if not strategy_id:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING, "No active strategy to paper trade",
            )
        strategy = self._cache.get_strategy(strategy_id)
        if strategy is None:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING, f"Strategy not found: {strategy_id}",
            )
        if not strategy.legs:
            return WorkspaceOperationResult(
                False, WorkspaceType.TRADING, "Strategy has no legs to paper trade",
            )

        now = datetime.now(timezone.utc)
        for leg in strategy.legs:
            side = OrderSide.BUY if "BUY" in leg.kind.value else OrderSide.SELL
            self._engines.paper_trading.service.submit_order(
                session_id,
                PaperOrderRequest(
                    leg=leg, side=side, quantity=abs(leg.quantity),
                    reference_price=leg.premium, timestamp=now,
                ),
            )
        snapshot: PaperAccountSnapshot = self._engines.paper_trading.service.snapshot(session_id)
        return WorkspaceOperationResult(
            True, WorkspaceType.TRADING,
            f"Paper traded {len(strategy.legs)} leg(s) — equity {snapshot.equity}",
            snapshot,
        )

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
