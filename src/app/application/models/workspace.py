"""Simplified UI-facing workspace models."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.application.models.enums import WorkspaceType


@dataclass(frozen=True, slots=True)
class WorkspaceView:
    """Simplified workspace view for UI."""

    workspace: WorkspaceType
    title: str
    summary: str
    entity_id: str
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class WorkspaceOperationResult:
    """Result of a workspace operation."""

    success: bool
    workspace: WorkspaceType
    message: str
    data: Any = None


@dataclass(frozen=True, slots=True)
class BacktestSessionView:
    """Backtest session state for UI."""

    session_id: str
    state: str
    progress: str
    can_pause: bool
    can_resume: bool
    can_stop: bool
