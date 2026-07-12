"""Application workspace services."""

__all__ = [
    "AIWorkspaceService",
    "BacktestingWorkspaceService",
    "MarketWorkspaceService",
    "OrderIntent",
    "OrderWorkspaceService",
    "PortfolioWorkspaceService",
    "SettingsWorkspaceService",
    "StrategyWorkspaceService",
    "TradingWorkspaceService",
]


def __getattr__(name: str) -> object:
    """Lazy exports to avoid import cycles."""
    if name == "AIWorkspaceService":
        from app.application.services.ai_workspace_service import AIWorkspaceService

        return AIWorkspaceService
    if name == "BacktestingWorkspaceService":
        from app.application.services.backtesting_workspace_service import (
            BacktestingWorkspaceService,
        )

        return BacktestingWorkspaceService
    if name == "MarketWorkspaceService":
        from app.application.services.market_workspace_service import MarketWorkspaceService

        return MarketWorkspaceService
    if name == "OrderIntent":
        from app.application.services.order_workspace_service import OrderIntent

        return OrderIntent
    if name == "OrderWorkspaceService":
        from app.application.services.order_workspace_service import OrderWorkspaceService

        return OrderWorkspaceService
    if name == "PortfolioWorkspaceService":
        from app.application.services.portfolio_workspace_service import (
            PortfolioWorkspaceService,
        )

        return PortfolioWorkspaceService
    if name == "SettingsWorkspaceService":
        from app.application.services.settings_workspace_service import (
            SettingsWorkspaceService,
        )

        return SettingsWorkspaceService
    if name == "StrategyWorkspaceService":
        from app.application.services.strategy_workspace_service import (
            StrategyWorkspaceService,
        )

        return StrategyWorkspaceService
    if name == "TradingWorkspaceService":
        from app.application.services.trading_workspace_service import TradingWorkspaceService

        return TradingWorkspaceService
    raise AttributeError(name)
