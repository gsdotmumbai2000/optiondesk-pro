"""Workspace registry."""

from app.application.models.enums import WorkspaceType
from app.application.services import (
    AIWorkspaceService,
    BacktestingWorkspaceService,
    MarketWorkspaceService,
    OrderWorkspaceService,
    PortfolioWorkspaceService,
    SettingsWorkspaceService,
    StrategyWorkspaceService,
    TradingWorkspaceService,
)


class WorkspaceRegistry:
    """Registry of workspace services."""

    def __init__(
        self,
        trading: TradingWorkspaceService,
        strategy: StrategyWorkspaceService,
        portfolio: PortfolioWorkspaceService,
        backtesting: BacktestingWorkspaceService,
        market: MarketWorkspaceService,
        ai: AIWorkspaceService,
        order: OrderWorkspaceService,
        settings: SettingsWorkspaceService,
    ) -> None:
        """Initialize registry."""
        self._services = {
            WorkspaceType.TRADING: trading,
            WorkspaceType.STRATEGY: strategy,
            WorkspaceType.PORTFOLIO: portfolio,
            WorkspaceType.BACKTESTING: backtesting,
            WorkspaceType.MARKET: market,
            WorkspaceType.AI: ai,
            WorkspaceType.ORDER: order,
            WorkspaceType.SETTINGS: settings,
        }

    def get(self, workspace: WorkspaceType):
        """Return workspace service by type."""
        return self._services[workspace]

    def all_types(self) -> tuple[WorkspaceType, ...]:
        """Return all workspace types."""
        return tuple(self._services.keys())
