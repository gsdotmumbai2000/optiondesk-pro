"""Navigation service."""

from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceView
from app.application.orchestration.workspace_coordinator import WorkspaceCoordinator
from app.application.session.session_manager import SessionManager


class NavigationService:
    """Navigate between application workspaces."""

    def __init__(
        self,
        sessions: SessionManager,
        workspaces: WorkspaceCoordinator,
    ) -> None:
        """Initialize navigation service."""
        self._sessions = sessions
        self._workspaces = workspaces

    def navigate(
        self,
        session_id: str,
        workspace: WorkspaceType,
        entity_id: str = "",
    ) -> WorkspaceView:
        """Navigate to workspace."""
        return self._workspaces.open_workspace(session_id, workspace, entity_id)

    def current_workspace(self, session_id: str) -> WorkspaceType:
        """Return current active workspace."""
        return self._sessions.get(session_id).active_workspace

    def available_workspaces(self) -> tuple[WorkspaceType, ...]:
        """Return all workspace types."""
        return tuple(WorkspaceType)
