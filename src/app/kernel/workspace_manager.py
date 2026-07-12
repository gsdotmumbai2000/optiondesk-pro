"""Workspace manager."""

import json
from pathlib import Path

from app.events.application_events import (WorkspaceLoadedEvent,
                                           WorkspaceSavedEvent)
from app.events.event_bus import EventBus
from app.kernel.workspace_models import WorkspaceProfile
from app.logging.logging_manager import get_logger
from app.utils.file_helper import FileHelper
from app.utils.uuid_helper import generate_uuid

logger = get_logger(__name__)


class WorkspaceManager:
    """Manage workspace layout persistence."""

    def __init__(self, workspace_directory: Path, event_bus: EventBus) -> None:
        """Initialize the workspace manager."""
        self._workspace_directory = workspace_directory
        self._event_bus = event_bus
        self._active_profile: WorkspaceProfile | None = None
        FileHelper.ensure_directory(workspace_directory)

    @property
    def active_profile(self) -> WorkspaceProfile | None:
        """Return the active workspace profile."""
        return self._active_profile

    def save_workspace(self, profile: WorkspaceProfile) -> None:
        """Save a workspace profile to disk."""
        path = self._profile_path(profile.workspace_name)
        FileHelper.write_json(path, profile.model_dump(mode="json"))
        self._active_profile = profile
        self._event_bus.publish(
            WorkspaceSavedEvent(payload={"workspace_name": profile.workspace_name})
        )
        logger.info("Workspace saved: {name}", name=profile.workspace_name)

    def load_workspace(self, workspace_name: str) -> WorkspaceProfile:
        """Load a workspace profile from disk."""
        path = self._profile_path(workspace_name)
        data = FileHelper.read_json(path)
        profile = WorkspaceProfile.model_validate(data)
        self._active_profile = profile
        self._event_bus.publish(
            WorkspaceLoadedEvent(payload={"workspace_name": profile.workspace_name})
        )
        logger.info("Workspace loaded: {name}", name=profile.workspace_name)
        return profile

    def load_active_profile(self) -> WorkspaceProfile | None:
        """Load the active workspace profile if available."""
        index_path = self._workspace_directory / "active.json"
        if not index_path.exists():
            return None
        active_name = json.loads(FileHelper.read_text(index_path)).get("workspace_name")
        if not active_name:
            return None
        return self.load_workspace(str(active_name))

    def save_active_profile(self) -> None:
        """Persist the active workspace index."""
        if self._active_profile is None:
            return
        self.save_workspace(self._active_profile)
        index_path = self._workspace_directory / "active.json"
        FileHelper.write_json(
            index_path, {"workspace_name": self._active_profile.workspace_name}
        )

    def reset_workspace(self, workspace_name: str = "Default") -> WorkspaceProfile:
        """Reset a workspace to factory defaults."""
        profile = WorkspaceProfile(
            workspace_id=generate_uuid(),
            workspace_name=workspace_name,
            is_active=True,
        )
        self.save_workspace(profile)
        return profile

    def export_workspace(self, workspace_name: str, export_path: Path) -> None:
        """Export a workspace profile to a file."""
        profile = self.load_workspace(workspace_name)
        FileHelper.write_json(export_path, profile.model_dump(mode="json"))

    def import_workspace(self, import_path: Path) -> WorkspaceProfile:
        """Import a workspace profile from a file."""
        data = FileHelper.read_json(import_path)
        profile = WorkspaceProfile.model_validate(data)
        profile.workspace_id = generate_uuid()
        self.save_workspace(profile)
        return profile

    def list_profiles(self) -> list[str]:
        """List available workspace profile names."""
        return [
            path.stem
            for path in self._workspace_directory.glob("*.json")
            if path.name != "active.json"
        ]

    def _profile_path(self, workspace_name: str) -> Path:
        """Return the storage path for a workspace profile."""
        safe_name = workspace_name.replace(" ", "_").lower()
        return self._workspace_directory / f"{safe_name}.json"
