"""Chart widgets package."""

from app.ui.charts.greeks_chart import GreeksChartWidget
from app.ui.charts.payoff_chart import PayoffChartWidget
from app.ui.charts.pnl_chart import PnlChartWidget
from app.ui.charts.price_chart import PriceChartWidget
from app.ui.charts.volatility_chart import VolatilityChartWidget


def price_chart(parent=None) -> PriceChartWidget:
    """Create a real live-price candlestick chart. Feed it ticks via a
    TickCandleBuffer (app.ui.market.tick_candle_buffer) and set_candles()."""
    return PriceChartWidget("Price Chart", parent)


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
