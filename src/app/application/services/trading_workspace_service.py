"""Trading workspace service."""

from datetime import datetime, timezone

from app.ai.models.batch import RecommendationBatchResult
from app.ai.models.request import RecommendationAnalysisRequest
from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult, WorkspaceView
from app.application.registry.engine_registry import EngineRegistry
from app.application.session.session_manager import SessionManager
from app.backtesting.models.request import BacktestRequest
from app.backtesting.models.result import BacktestResult
from app.strategy.models.evaluation import StrategyEvaluation
from app.strategy.models.request import StrategyEvaluationRequest
from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.models.request import OptimizationRequest
from app.strategy_optimizer.models.result import OptimizationResult


class TradingWorkspaceService:
    """Trading workflow orchestration API for UI."""

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
