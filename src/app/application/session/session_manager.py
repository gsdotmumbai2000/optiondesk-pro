"""Application session manager."""

from dataclasses import replace
from datetime import datetime, timezone
from threading import RLock

from app.application.exceptions import SessionNotFoundError
from app.application.models.enums import WorkspaceType
from app.application.models.session import (
    ApplicationSession,
    RecentStrategy,
    UserPreferences,
    WorkspaceState,
)
from app.utils.uuid_helper import generate_uuid


class SessionManager:
    """Manage application sessions and workspace state."""

    def __init__(self) -> None:
        """Initialize session manager."""
        self._lock = RLock()
        self._sessions: dict[str, ApplicationSession] = {}

    def create(
        self,
        workspace: WorkspaceType = WorkspaceType.TRADING,
        preferences: UserPreferences | None = None,
    ) -> ApplicationSession:
        """Create new application session."""
        session_id = generate_uuid()
        now = datetime.now(timezone.utc)
        state = WorkspaceState(workspace=workspace, is_active=True, last_updated_at=now)
        session = ApplicationSession(
            session_id=session_id,
            started_at=now,
            active_workspace=workspace,
            workspaces=(state,),
            preferences=preferences or UserPreferences(),
        )
        with self._lock:
            self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> ApplicationSession:
        """Return session by id."""
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(f"session not found: {session_id}")
        return session

    def set_active_workspace(
        self,
        session_id: str,
        workspace: WorkspaceType,
        entity_id: str = "",
    ) -> ApplicationSession:
        """Update active workspace."""
        session = self.get(session_id)
        now = datetime.now(timezone.utc)
        state = WorkspaceState(
            workspace=workspace,
            is_active=True,
            entity_id=entity_id,
            last_updated_at=now,
        )
        workspaces = tuple(
            replace(s, is_active=False) if s.workspace != workspace else state
            for s in session.workspaces
        )
        if not any(s.workspace == workspace for s in workspaces):
            workspaces = workspaces + (state,)
        updated = replace(
            session,
            active_workspace=workspace,
            workspaces=workspaces,
        )
        with self._lock:
            self._sessions[session_id] = updated
        return updated

    def add_recent_strategy(
        self,
        session_id: str,
        strategy_id: str,
        name: str,
    ) -> ApplicationSession:
        """Track recent strategy access."""
        session = self.get(session_id)
        recent = RecentStrategy(
            strategy_id=strategy_id,
            name=name,
            accessed_at=datetime.now(timezone.utc),
        )
        recents = (recent,) + tuple(
            r for r in session.recent_strategies if r.strategy_id != strategy_id
        )[:9]
        updated = replace(session, recent_strategies=recents)
        with self._lock:
            self._sessions[session_id] = updated
        return updated

    def update_preferences(
        self,
        session_id: str,
        preferences: UserPreferences,
    ) -> ApplicationSession:
        """Update user preferences."""
        session = self.get(session_id)
        updated = replace(session, preferences=preferences)
        with self._lock:
            self._sessions[session_id] = updated
        return updated
