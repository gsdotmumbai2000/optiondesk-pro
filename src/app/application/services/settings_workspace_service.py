"""Settings workspace service."""

from datetime import datetime, timezone

from app.application.models.enums import WorkspaceType
from app.application.models.session import UserPreferences
from app.application.models.workspace import WorkspaceOperationResult, WorkspaceView
from app.application.session.session_manager import SessionManager


class SettingsWorkspaceService:
    """Settings and preferences workspace API."""

    def __init__(self, sessions: SessionManager) -> None:
        """Initialize service."""
        self._sessions = sessions

    def get_preferences(self, session_id: str) -> UserPreferences:
        """Return user preferences."""
        return self._sessions.get(session_id).preferences

    def update_preferences(
        self,
        session_id: str,
        preferences: UserPreferences,
    ) -> WorkspaceOperationResult:
        """Update user preferences."""
        self._sessions.update_preferences(session_id, preferences)
        return WorkspaceOperationResult(
            True,
            WorkspaceType.SETTINGS,
            "Preferences updated",
            preferences,
        )

    def view(self, session_id: str) -> WorkspaceView:
        """Return settings workspace view."""
        prefs = self.get_preferences(session_id)
        return WorkspaceView(
            workspace=WorkspaceType.SETTINGS,
            title="Settings",
            summary=f"Exchange: {prefs.default_exchange}, theme: {prefs.theme}",
            entity_id="",
            updated_at=datetime.now(timezone.utc),
        )
