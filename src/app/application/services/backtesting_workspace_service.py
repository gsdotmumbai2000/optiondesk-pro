"""Backtesting workspace service."""

from datetime import datetime, timezone
from threading import RLock

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import BacktestRunState, WorkspaceType
from app.application.models.workspace import BacktestSessionView, WorkspaceOperationResult, WorkspaceView
from app.application.registry.engine_registry import EngineRegistry
from app.application.session.session_manager import SessionManager
from app.backtesting.models.request import BacktestRequest
from app.backtesting.models.result import BacktestResult


class BacktestingWorkspaceService:
    """Backtesting workspace API for UI."""

    def __init__(
        self,
        engines: EngineRegistry,
        sessions: SessionManager,
        cache: WorkspaceCache,
    ) -> None:
        """Initialize service."""
        self._engines = engines
        self._sessions = sessions
        self._cache = cache
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
