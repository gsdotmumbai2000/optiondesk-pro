"""Command models."""

from dataclasses import dataclass, field
from typing import Any

from app.application.models.enums import CommandType


@dataclass(frozen=True, slots=True)
class ApplicationCommand:
    """Base application command."""

    command_type: CommandType
    session_id: str
    payload: dict[str, Any] = field(default_factory=dict)


def open_strategy_command(session_id: str, strategy_id: str) -> ApplicationCommand:
    """Build open strategy command."""
    return ApplicationCommand(
        CommandType.OPEN_STRATEGY,
        session_id,
        {"strategy_id": strategy_id},
    )


def save_strategy_command(session_id: str, strategy_id: str) -> ApplicationCommand:
    """Build save strategy command."""
    return ApplicationCommand(
        CommandType.SAVE_STRATEGY,
        session_id,
        {"strategy_id": strategy_id},
    )


def run_optimization_command(session_id: str) -> ApplicationCommand:
    """Build run optimization command."""
    return ApplicationCommand(CommandType.RUN_OPTIMIZATION, session_id)


def run_backtest_command(session_id: str) -> ApplicationCommand:
    """Build run backtest command."""
    return ApplicationCommand(CommandType.RUN_BACKTEST, session_id)


def refresh_market_command(session_id: str) -> ApplicationCommand:
    """Build refresh market command."""
    return ApplicationCommand(CommandType.REFRESH_MARKET, session_id)


def generate_report_command(session_id: str, report_type: str) -> ApplicationCommand:
    """Build generate report command."""
    return ApplicationCommand(
        CommandType.GENERATE_REPORT,
        session_id,
        {"report_type": report_type},
    )
