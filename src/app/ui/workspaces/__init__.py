"""Workspaces package."""

from app.ui.workspaces.workspace_factory import (
    ai_workspace,
    backtesting_workspace,
    market_workspace,
    portfolio_workspace,
    reports_workspace,
    settings_workspace,
    strategy_workspace,
    trading_workspace,
)

__all__ = [
    "ai_workspace",
    "backtesting_workspace",
    "market_workspace",
    "portfolio_workspace",
    "reports_workspace",
    "settings_workspace",
    "strategy_workspace",
    "trading_workspace",
]
