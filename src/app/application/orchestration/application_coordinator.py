"""Application coordinator."""

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.events import (
    BacktestStartedEvent,
    PortfolioLoadedEvent,
    RecommendationReadyEvent,
    StrategyLoadedEvent,
)
from app.application.models.session import ApplicationSession, UserPreferences
from app.application.models.enums import WorkspaceType
from app.application.registry.engine_registry import EngineRegistry
from app.application.orchestration.workspace_coordinator import WorkspaceCoordinator
from app.application.session.session_manager import SessionManager
from app.events.event_bus import EventBus


class ApplicationCoordinator:
    """Top-level application lifecycle coordinator."""

    def __init__(
        self,
        engines: EngineRegistry,
        sessions: SessionManager,
        workspaces: WorkspaceCoordinator,
        cache: WorkspaceCache,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize coordinator."""
        self._engines = engines
        self._sessions = sessions
        self._workspaces = workspaces
        self._cache = cache
        self._event_bus = event_bus

    @property
    def engines(self) -> EngineRegistry:
        """Return engine registry."""
        return self._engines

    @property
    def sessions(self) -> SessionManager:
        """Return session manager."""
        return self._sessions

    @property
    def workspaces(self) -> WorkspaceCoordinator:
        """Return workspace coordinator."""
        return self._workspaces

    @property
    def cache(self) -> WorkspaceCache:
        """Return workspace cache."""
        return self._cache

    def start_session(
        self,
        workspace: WorkspaceType = WorkspaceType.TRADING,
        preferences: UserPreferences | None = None,
    ) -> ApplicationSession:
        """Start new application session."""
        return self._sessions.create(workspace, preferences)

    def notify_strategy_loaded(self, strategy_id: str) -> None:
        """Publish strategy loaded event."""
        if self._event_bus is None:
            return
        self._event_bus.publish(
            StrategyLoadedEvent(payload={"strategy_id": strategy_id})
        )

    def notify_portfolio_loaded(self, portfolio_id: str) -> None:
        """Publish portfolio loaded event."""
        if self._event_bus is None:
            return
        self._event_bus.publish(
            PortfolioLoadedEvent(payload={"portfolio_id": portfolio_id})
        )

    def notify_backtest_started(self, session_id: str) -> None:
        """Publish backtest started event."""
        if self._event_bus is None:
            return
        self._event_bus.publish(
            BacktestStartedEvent(payload={"session_id": session_id})
        )

    def notify_recommendation_ready(self, session_id: str, count: int) -> None:
        """Publish recommendation ready event."""
        if self._event_bus is None:
            return
        self._event_bus.publish(
            RecommendationReadyEvent(
                payload={"session_id": session_id, "count": str(count)}
            )
        )
