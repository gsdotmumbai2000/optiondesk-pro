"""Adapt application session/cache state for the live calculation pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.strategy.models.leg import StrategyLeg
from app.strategy.models.strategy import Strategy

if TYPE_CHECKING:
    from app.application.cache.workspace_cache import WorkspaceCache
    from app.application.session.session_manager import SessionManager

_STRATEGY_WORKSPACE_NAMES = ("TRADING", "STRATEGY")


class ActiveStrategyAdapter:
    """Resolve the currently active strategy's legs from session state.

    Reads only existing session/cache state (no new active-strategy store):
    WorkspaceState.entity_id already carries the strategy id for whichever
    session last touched the Trading or Strategy workspace (set by
    TradingWorkspaceService/StrategyWorkspaceService on create/save/load/
    evaluate), and WorkspaceCache.get_strategy() already caches the full
    Strategy object by that id. The lookup is performed fresh on every call
    so it reflects the currently active strategy, never a value captured at
    construction time.

    `app.application` is imported lazily inside the lookup method rather than
    at module level: app/application/__init__.py eagerly re-exports
    ApplicationProvider (which itself imports LiveAnalyticsProvider from
    app.live.bootstrap), so a module-level `app.application.*` import here
    would recreate that exact cycle. WorkspaceType is compared by its
    (str, Enum) value rather than imported, for the same reason.
    """

    def __init__(self, sessions: "SessionManager", cache: "WorkspaceCache") -> None:
        self._sessions = sessions
        self._cache = cache

    def get_active_strategy_legs(self) -> tuple[StrategyLeg, ...]:
        """Return the active strategy's legs, or () when no strategy is active."""
        strategy_id = self._resolve_active_strategy_id()
        if not strategy_id:
            return ()
        strategy = self._cache.get_strategy(strategy_id)
        if not isinstance(strategy, Strategy):
            return ()
        return strategy.legs

    def _resolve_active_strategy_id(self) -> str:
        """Return the entity_id of the most recently updated Trading/Strategy
        workspace state across all sessions, or "" if none is active."""
        latest_id = ""
        latest_updated_at = None
        for session in self._sessions.all_sessions():
            for state in session.workspaces:
                if state.workspace.value not in _STRATEGY_WORKSPACE_NAMES or not state.entity_id:
                    continue
                if latest_updated_at is None or (
                    state.last_updated_at is not None
                    and state.last_updated_at > latest_updated_at
                ):
                    latest_updated_at = state.last_updated_at
                    latest_id = state.entity_id
        return latest_id
