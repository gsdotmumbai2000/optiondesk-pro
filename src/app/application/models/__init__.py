"""Application domain models."""

from app.application.models.commands import (
    ApplicationCommand,
    generate_report_command,
    open_strategy_command,
    refresh_market_command,
    run_backtest_command,
    run_optimization_command,
    save_strategy_command,
)
from app.application.models.enums import (
    ApplicationModelVersion,
    BacktestRunState,
    CommandType,
    QueryType,
    WorkspaceType,
)
from app.application.models.queries import ApplicationQuery, QueryResult
from app.application.models.session import (
    ApplicationSession,
    RecentFile,
    RecentStrategy,
    UserPreferences,
    WorkspaceState,
)
from app.application.models.workspace import (
    BacktestSessionView,
    WorkspaceOperationResult,
    WorkspaceView,
)

__all__ = [
    "ApplicationCommand",
    "ApplicationModelVersion",
    "ApplicationQuery",
    "ApplicationSession",
    "BacktestRunState",
    "BacktestSessionView",
    "CommandType",
    "QueryResult",
    "QueryType",
    "RecentFile",
    "RecentStrategy",
    "UserPreferences",
    "WorkspaceOperationResult",
    "WorkspaceState",
    "WorkspaceType",
    "WorkspaceView",
    "generate_report_command",
    "open_strategy_command",
    "refresh_market_command",
    "run_backtest_command",
    "run_optimization_command",
    "save_strategy_command",
]
