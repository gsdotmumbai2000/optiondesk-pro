"""Workspace data models."""

from pydantic import BaseModel, Field


class WorkspaceProfile(BaseModel):
    """Persisted workspace profile."""

    workspace_id: str
    workspace_name: str
    is_active: bool = False
    monitor_count: int = 1
    monitor_layout: dict[str, object] = Field(default_factory=dict)
    dock_state_hex: str = ""
    window_geometry_hex: str = ""
    active_view: str = ""
    schema_version: int = 1
