"""Chart widgets package."""

from app.ui.charts.base_chart import ChartPlaceholder
from app.ui.charts.greeks_chart import GreeksChartWidget
from app.ui.charts.payoff_chart import PayoffChartWidget
from app.ui.charts.pnl_chart import PnlChartWidget
from app.ui.charts.volatility_chart import VolatilityChartWidget
from app.ui.models.ui_enums import ChartType


def price_chart(parent=None) -> ChartPlaceholder:
    """Create price chart placeholder.

    Not yet real: a live tick-history price chart needs a candle/tick
    buffer this pass didn't build. Left as a placeholder rather than
    faking data.
    """
    return ChartPlaceholder(ChartType.PRICE, "Price Chart", parent)


def payoff_chart(parent=None) -> PayoffChartWidget:
    """Create a real payoff diagram chart."""
    return PayoffChartWidget(parent)


def greeks_chart(parent=None) -> GreeksChartWidget:
    """Create a real Greeks bar chart."""
    return GreeksChartWidget(parent)


def volatility_chart(parent=None) -> VolatilityChartWidget:
    """Create a real volatility smile/skew chart."""
    return VolatilityChartWidget(parent)


def pnl_chart(parent=None, title: str = "PnL") -> PnlChartWidget:
    """Create a real PnL/equity time-series chart."""
    return PnlChartWidget(title, parent)
