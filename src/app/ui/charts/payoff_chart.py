"""Real payoff diagram chart (strategy P&L vs underlying price)."""

from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.payoff.models.result import PayoffCurve
from app.ui.charts import theme


class PayoffChartWidget(QChartView):
    """Payoff diagram: P&L curve across a range of underlying prices, with
    a zero-reference line marking the profit/loss boundary."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize an empty payoff chart."""
        chart = QChart()
        chart.setTitle("Payoff Diagram")
        chart.legend().setVisible(False)
        chart.setBackgroundBrush(theme.BACKGROUND)
        chart.setTitleBrush(theme.TEXT)
        super().__init__(chart, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._pnl_series = QLineSeries()
        self._pnl_series.setPen(QPen(theme.ACCENT, 2))
        self._zero_series = QLineSeries()
        self._zero_series.setPen(QPen(theme.MUTED_TEXT, 1, Qt.PenStyle.DashLine))
        chart.addSeries(self._pnl_series)
        chart.addSeries(self._zero_series)

        self._x_axis = QValueAxis()
        self._x_axis.setTitleText("Underlying Price")
        self._x_axis.setLabelsColor(theme.MUTED_TEXT)
        self._x_axis.setTitleBrush(theme.MUTED_TEXT)
        self._x_axis.setGridLineColor(theme.BORDER)
        self._y_axis = QValueAxis()
        self._y_axis.setTitleText("P&L")
        self._y_axis.setLabelsColor(theme.MUTED_TEXT)
        self._y_axis.setTitleBrush(theme.MUTED_TEXT)
        self._y_axis.setGridLineColor(theme.BORDER)
        chart.addAxis(self._x_axis, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(self._y_axis, Qt.AlignmentFlag.AlignLeft)
        for series in (self._pnl_series, self._zero_series):
            series.attachAxis(self._x_axis)
            series.attachAxis(self._y_axis)

    def set_curve(self, curve: PayoffCurve) -> None:
        """Render a payoff curve. Clears the chart when the curve is empty."""
        self._pnl_series.clear()
        self._zero_series.clear()
        if not curve.points:
            return
        prices = [float(point.underlying_price) for point in curve.points]
        pnls = [float(point.pnl) for point in curve.points]
        for price, pnl in zip(prices, pnls):
            self._pnl_series.append(price, pnl)
        self._zero_series.append(min(prices), 0.0)
        self._zero_series.append(max(prices), 0.0)

        self._x_axis.setRange(min(prices), max(prices))
        y_min, y_max = min(pnls + [0.0]), max(pnls + [0.0])
        pad = max((y_max - y_min) * 0.1, 1.0)
        self._y_axis.setRange(y_min - pad, y_max + pad)

    def clear(self) -> None:
        """Clear the chart (e.g. when no strategy is active)."""
        self._pnl_series.clear()
        self._zero_series.clear()
