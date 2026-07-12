"""UI-specific enumerations."""

from enum import Enum


class UITheme(str, Enum):
    """Desktop theme identifiers."""

    LIGHT = "light"
    DARK = "dark"
    HIGH_CONTRAST = "high_contrast"


class UIWorkspaceId(str, Enum):
    """UI workspace tab identifiers."""

    TRADING = "trading"
    MARKET = "market"
    STRATEGY = "strategy"
    PORTFOLIO = "portfolio"
    BACKTESTING = "backtesting"
    AI = "ai"
    REPORTS = "reports"
    SETTINGS = "settings"


class ChartType(str, Enum):
    """Chart placeholder types."""

    PRICE = "price"
    PAYOFF = "payoff"
    GREEKS = "greeks"
    VOLATILITY = "volatility"
    PNL = "pnl"
