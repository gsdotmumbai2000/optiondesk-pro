"""Application event definitions."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.utils.datetime_helper import DateTimeHelper
from app.utils.uuid_helper import generate_uuid


@dataclass(frozen=True, slots=True)
class ApplicationEvent:
    """Base class for all application events."""

    event_id: str = field(default_factory=generate_uuid)
    timestamp: datetime = field(default_factory=DateTimeHelper.utc_now)
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ApplicationStartedEvent(ApplicationEvent):
    """Published when the application has started."""


@dataclass(frozen=True, slots=True)
class ApplicationShuttingDownEvent(ApplicationEvent):
    """Published when the application is shutting down."""


@dataclass(frozen=True, slots=True)
class ApplicationStoppedEvent(ApplicationEvent):
    """Published when the application has stopped."""


@dataclass(frozen=True, slots=True)
class ConfigurationChangedEvent(ApplicationEvent):
    """Published when configuration changes."""


@dataclass(frozen=True, slots=True)
class PluginLoadedEvent(ApplicationEvent):
    """Published when a plugin is loaded."""


@dataclass(frozen=True, slots=True)
class PluginUnloadedEvent(ApplicationEvent):
    """Published when a plugin is unloaded."""


@dataclass(frozen=True, slots=True)
class HealthStatusChangedEvent(ApplicationEvent):
    """Published when health status changes."""


@dataclass(frozen=True, slots=True)
class WorkspaceSavedEvent(ApplicationEvent):
    """Published when a workspace is saved."""


@dataclass(frozen=True, slots=True)
class WorkspaceLoadedEvent(ApplicationEvent):
    """Published when a workspace is loaded."""
