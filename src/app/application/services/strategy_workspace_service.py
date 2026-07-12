"""Strategy workspace service."""

from datetime import datetime, timezone

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult, WorkspaceView
from app.application.registry.engine_registry import EngineRegistry
from app.application.session.session_manager import SessionManager
from app.strategy.models.strategy import Strategy


class StrategyWorkspaceService:
    """Strategy CRUD and template workspace API."""

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

    def load_strategy(
        self,
        session_id: str,
        strategy_id: str,
    ) -> WorkspaceOperationResult:
        """Load strategy by id."""
        strategy = self._engines.strategy.repository.get(strategy_id)
        if strategy is None:
            return WorkspaceOperationResult(
                False,
                WorkspaceType.STRATEGY,
                f"Strategy not found: {strategy_id}",
            )
        self._cache.put_strategy(strategy_id, strategy)
        self._sessions.add_recent_strategy(session_id, strategy_id, strategy.metadata.name)
        self._sessions.set_active_workspace(session_id, WorkspaceType.STRATEGY, strategy_id)
        return WorkspaceOperationResult(
            True,
            WorkspaceType.STRATEGY,
            "Strategy loaded",
            strategy,
        )

    def save_strategy(
        self,
        session_id: str,
        strategy: Strategy,
    ) -> WorkspaceOperationResult:
        """Save strategy."""
        saved = self._engines.strategy.service.update(strategy)
        self._cache.put_strategy(saved.strategy_id, saved)
        self._sessions.add_recent_strategy(session_id, saved.strategy_id, saved.metadata.name)
        return WorkspaceOperationResult(
            True,
            WorkspaceType.STRATEGY,
            "Strategy saved",
            saved,
        )

    def create_strategy(self, session_id: str, strategy: Strategy) -> WorkspaceOperationResult:
        """Create new strategy."""
        created = self._engines.strategy.service.create(strategy)
        self._cache.put_strategy(created.strategy_id, created)
        self._sessions.set_active_workspace(
            session_id,
            WorkspaceType.STRATEGY,
            created.strategy_id,
        )
        return WorkspaceOperationResult(
            True,
            WorkspaceType.STRATEGY,
            "Strategy created",
            created,
        )

    def list_strategies(self, session_id: str) -> WorkspaceOperationResult:
        """List all strategies."""
        strategies = self._engines.strategy.repository.list_all()
        return WorkspaceOperationResult(
            True,
            WorkspaceType.STRATEGY,
            f"{len(strategies)} strategies",
            strategies,
        )

    def get_strategy(self, strategy_id: str):
        """Return strategy by id."""
        return self._engines.strategy.repository.get(strategy_id)

    def view(self, session_id: str) -> WorkspaceView:
        """Return strategy workspace view."""
        session = self._sessions.get(session_id)
        count = len(self._engines.strategy.repository.list_all())
        return WorkspaceView(
            workspace=WorkspaceType.STRATEGY,
            title="Strategy Workspace",
            summary=f"{count} strategies, {len(session.recent_strategies)} recent",
            entity_id="",
            updated_at=datetime.now(timezone.utc),
        )
