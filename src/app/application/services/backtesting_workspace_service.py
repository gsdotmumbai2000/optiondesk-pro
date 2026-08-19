"""Backtesting workspace service."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from threading import RLock

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import BacktestRunState, WorkspaceType
from app.application.models.workspace import BacktestSessionView, WorkspaceOperationResult, WorkspaceView
from app.application.ports.broker_historical_port import BrokerHistoricalPort
from app.application.registry.engine_registry import EngineRegistry
from app.application.session.session_manager import SessionManager
from app.backtesting.models.config import ExecutionConfig, ReplayConfig, SimulationParameters
from app.backtesting.models.historical import HistoricalOptionChainData
from app.backtesting.models.request import BacktestRequest
from app.backtesting.models.result import BacktestResult


class BacktestingWorkspaceService:
    """Backtesting workspace API for UI."""

    def __init__(
        self,
        engines: EngineRegistry,
        sessions: SessionManager,
        cache: WorkspaceCache,
        broker_historical: BrokerHistoricalPort | None = None,
    ) -> None:
        """Initialize service."""
        self._engines = engines
        self._sessions = sessions
        self._cache = cache
        self._broker_historical = broker_historical
        self._lock = RLock()
        self._run_state: dict[str, BacktestRunState] = {}

    def run_backtest(
        self,
        session_id: str,
        request: BacktestRequest,
    ) -> BacktestResult:
        """Run backtest via backtesting engine."""
        with self._lock:
            self._run_state[session_id] = BacktestRunState.RUNNING
        result = self._engines.backtest.service.run(request)
        self._cache.put_data(f"{session_id}:backtest", result)
        with self._lock:
            self._run_state[session_id] = BacktestRunState.COMPLETED
        return result

    def run_active_strategy_backtest(
        self,
        session_id: str,
        *,
        lookback_days: int = 30,
        exchange: str = "NFO",
    ) -> WorkspaceOperationResult:
        """Backtest the strategy currently active in the Trading/Strategy
        workspace against real historical bars for its underlying, fetched
        on demand from the connected broker (a REST call, not the live tick
        pipeline) covering the last `lookback_days` calendar days up to now.

        option_chain_data is deliberately an empty snapshot series and
        strategy_context/optimization_result are None: BacktestEngine.run()
        only prices trades off market_data's underlying bars (see
        _maybe_execute()) and only reads strategy_context for optional
        margin/unrealized-PnL enrichment, so neither is required for a real
        (not fabricated) run against real history.

        WorkspaceOperationResult.success is False (no result data) when
        there's no active strategy, its legs are missing an underlying, no
        broker historical source is configured, or the broker returned no
        bars for the period -- callers should treat that as "nothing to
        show", not as an error."""
        session = self._sessions.get(session_id)
        strategy_id = next(
            (
                w.entity_id
                for w in session.workspaces
                if w.workspace in (WorkspaceType.TRADING, WorkspaceType.STRATEGY) and w.entity_id
            ),
            "",
        )
        if not strategy_id:
            return WorkspaceOperationResult(
                False, WorkspaceType.BACKTESTING, "No active strategy to backtest",
            )
        strategy = self._cache.get_strategy(strategy_id)
        if strategy is None:
            return WorkspaceOperationResult(
                False, WorkspaceType.BACKTESTING, f"Strategy not found: {strategy_id}",
            )
        if not strategy.legs:
            return WorkspaceOperationResult(
                False, WorkspaceType.BACKTESTING, "Strategy has no legs to backtest",
            )
        leg = strategy.legs[0]
        if not leg.underlying:
            return WorkspaceOperationResult(
                False, WorkspaceType.BACKTESTING, "Strategy legs are missing underlying",
            )
        if self._broker_historical is None:
            return WorkspaceOperationResult(
                False, WorkspaceType.BACKTESTING, "No broker historical data source configured",
            )
        to_date = datetime.now(timezone.utc)
        from_date = to_date - timedelta(days=lookback_days)
        market_data = self._broker_historical.get_historical_bars(
            leg.underlying, leg.exchange or exchange, from_date, to_date,
        )
        if market_data is None or not market_data.bars:
            return WorkspaceOperationResult(
                False, WorkspaceType.BACKTESTING,
                "Historical data unavailable — connect a broker to backtest against real history",
            )
        request = BacktestRequest(
            strategy=strategy,
            strategy_context=None,
            optimization_result=None,
            market_data=market_data,
            option_chain_data=HistoricalOptionChainData(underlying=leg.underlying, snapshots=()),
            parameters=SimulationParameters(
                initial_capital=Decimal("100000"),
                replay=ReplayConfig(),
                execution=ExecutionConfig(),
            ),
        )
        result = self.run_backtest(session_id, request)
        return WorkspaceOperationResult(True, WorkspaceType.BACKTESTING, "Backtest complete", result)

    def pause(self, session_id: str) -> BacktestSessionView:
        """Pause backtest session (framework)."""
        with self._lock:
            if self._run_state.get(session_id) == BacktestRunState.RUNNING:
                self._run_state[session_id] = BacktestRunState.PAUSED
        return self.session_view(session_id)

    def resume(self, session_id: str) -> BacktestSessionView:
        """Resume backtest session (framework)."""
        with self._lock:
            if self._run_state.get(session_id) == BacktestRunState.PAUSED:
                self._run_state[session_id] = BacktestRunState.RUNNING
        return self.session_view(session_id)

    def stop(self, session_id: str) -> BacktestSessionView:
        """Stop backtest session."""
        with self._lock:
            self._run_state[session_id] = BacktestRunState.STOPPED
        return self.session_view(session_id)

    def replay(self, session_id: str, request: BacktestRequest) -> BacktestResult:
        """Replay backtest via engine."""
        return self.run_backtest(session_id, request)

    def export_results(self, session_id: str) -> WorkspaceOperationResult:
        """Export backtest results from cache."""
        result = self._cache.get_data(f"{session_id}:backtest")
        if result is None:
            return WorkspaceOperationResult(
                False,
                WorkspaceType.BACKTESTING,
                "No backtest results to export",
            )
        report = self._engines.backtest.service.build_report(result)
        self._cache.put_report(f"{session_id}:backtest-report", report)
        return WorkspaceOperationResult(
            True,
            WorkspaceType.BACKTESTING,
            "Results exported",
            report,
        )

    def session_view(self, session_id: str) -> BacktestSessionView:
        """Return backtest session view."""
        state = self._run_state.get(session_id, BacktestRunState.IDLE)
        return BacktestSessionView(
            session_id=session_id,
            state=state.value,
            progress="",
            can_pause=state == BacktestRunState.RUNNING,
            can_resume=state == BacktestRunState.PAUSED,
            can_stop=state in (BacktestRunState.RUNNING, BacktestRunState.PAUSED),
        )

    def view(self, session_id: str) -> WorkspaceView:
        """Return backtesting workspace view."""
        bt_view = self.session_view(session_id)
        return WorkspaceView(
            workspace=WorkspaceType.BACKTESTING,
            title="Backtesting Workspace",
            summary=f"State: {bt_view.state}",
            entity_id=session_id,
            updated_at=datetime.now(timezone.utc),
        )
