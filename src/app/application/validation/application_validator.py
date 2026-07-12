"""Application layer validation."""

from app.application.exceptions import InvalidApplicationInput
from app.application.models.commands import ApplicationCommand
from app.application.models.enums import WorkspaceType
from app.application.models.queries import ApplicationQuery
from app.application.models.session import ApplicationSession, WorkspaceState


class ApplicationValidator:
    """Validate sessions, commands, and workspace state."""

    def validate_session(self, session: ApplicationSession) -> None:
        """Validate application session."""
        if not session.session_id:
            raise InvalidApplicationInput("session_id is required")

    def validate_command(self, command: ApplicationCommand) -> None:
        """Validate application command."""
        if not command.session_id:
            raise InvalidApplicationInput("command session_id is required")

    def validate_query(self, query: ApplicationQuery) -> None:
        """Validate application query."""
        if not query.session_id:
            raise InvalidApplicationInput("query session_id is required")

    def validate_workspace_state(self, state: WorkspaceState) -> None:
        """Validate workspace state."""
        if state.workspace not in WorkspaceType:
            raise InvalidApplicationInput("invalid workspace type")
