"""Chart placeholders package."""

from app.ui.charts.base_chart import ChartPlaceholder
from app.ui.models.ui_enums import ChartType


def price_chart(parent=None) -> ChartPlaceholder:
    """Create price chart placeholder."""
    return ChartPlaceholder(ChartType.PRICE, "Price Chart", parent)


def payoff_chart(parent=None) -> ChartPlaceholder:
    """Create payoff chart placeholder."""
    return ChartPlaceholder(ChartType.PAYOFF, "Payoff Chart", parent)


def greeks_chart(parent=None) -> ChartPlaceholder:
    """Create greeks chart placeholder."""
    return ChartPlaceholder(ChartType.GREEKS, "Greeks Chart", parent)


def volatility_chart(parent=None) -> ChartPlaceholder:
    """Create volatility chart placeholder."""
    return ChartPlaceholder(ChartType.VOLATILITY, "Volatility Chart", parent)


def pnl_chart(parent=None) -> ChartPlaceholder:
    """Create PnL chart placeholder."""
    return ChartPlaceholder(ChartType.PNL, "PnL Chart", parent)
