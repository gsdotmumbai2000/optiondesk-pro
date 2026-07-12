"""Session domain models."""

from dataclasses import dataclass, field
from datetime import datetime

from app.application.models.enums import ApplicationModelVersion, WorkspaceType


@dataclass(frozen=True, slots=True)
class RecentFile:
    """Recently accessed file reference."""

    path: str
    opened_at: datetime
    workspace: WorkspaceType


@dataclass(frozen=True, slots=True)
class RecentStrategy:
    """Recently accessed strategy reference."""

    strategy_id: str
    name: str
    accessed_at: datetime


@dataclass(frozen=True, slots=True)
class UserPreferences:
    """Application user preferences."""

    theme: str = "system"
    default_exchange: str = "NSE"
    risk_tolerance: str = "moderate"
    auto_refresh_interval_seconds: int = 60


@dataclass(frozen=True, slots=True)
class WorkspaceState:
    """Active workspace state snapshot."""

    workspace: WorkspaceType
    is_active: bool
    entity_id: str = ""
    last_updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ApplicationSession:
    """Immutable application session."""

    session_id: str
    started_at: datetime
    active_workspace: WorkspaceType
    workspaces: tuple[WorkspaceState, ...]
    recent_files: tuple[RecentFile, ...] = ()
    recent_strategies: tuple[RecentStrategy, ...] = ()
    preferences: UserPreferences = field(default_factory=UserPreferences)
    version: ApplicationModelVersion = ApplicationModelVersion.V1
