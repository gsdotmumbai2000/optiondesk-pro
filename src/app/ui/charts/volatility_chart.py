"""Real volatility smile/skew chart (IV vs strike, call and put)."""

from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.calculation.models.snapshots import OptionChainSnapshot
from app.ui.charts import theme


class VolatilityChartWidget(QChartView):
    """Volatility smile/skew: call and put IV plotted across strikes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize an empty volatility chart."""
        chart = QChart()
        chart.setTitle("Volatility Smile")
        chart.legend().setVisible(True)
        chart.legend().setLabelColor(theme.MUTED_TEXT)
        chart.setBackgroundBrush(theme.BACKGROUND)
        chart.setTitleBrush(theme.TEXT)
        super().__init__(chart, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._call_series = QLineSeries()
        self._call_series.setName("Call IV")
        self._call_series.setPen(QPen(theme.CALL, 2))
        self._put_series = QLineSeries()
        self._put_series.setName("Put IV")
        self._put_series.setPen(QPen(theme.PUT, 2))
        chart.addSeries(self._call_series)
        chart.addSeries(self._put_series)

        self._x_axis = QValueAxis()
        self._x_axis.setTitleText("Strike")
        self._x_axis.setLabelsColor(theme.MUTED_TEXT)
        self._x_axis.setTitleBrush(theme.MUTED_TEXT)
        self._x_axis.setGridLineColor(theme.BORDER)
        self._y_axis = QValueAxis()
        self._y_axis.setTitleText("Implied Volatility")
        self._y_axis.setLabelsColor(theme.MUTED_TEXT)
        self._y_axis.setTitleBrush(theme.MUTED_TEXT)
        self._y_axis.setGridLineColor(theme.BORDER)
        self._y_axis.setLabelFormat("%.0f%%")
        chart.addAxis(self._x_axis, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(self._y_axis, Qt.AlignmentFlag.AlignLeft)
        for series in (self._call_series, self._put_series):
            series.attachAxis(self._x_axis)
            series.attachAxis(self._y_axis)

    def set_chain(self, option_chain: OptionChainSnapshot) -> None:
        """Render call/put IV across strikes. Only strikes with a quoted
        IV on the respective side are plotted; clears when none are."""
        self._call_series.clear()
        self._put_series.clear()
        strikes = sorted(option_chain.strikes, key=lambda s: s.strike_price)
        call_points = [
            (float(s.strike_price), float(s.call_iv) * 100.0)
            for s in strikes if s.call_iv is not None and s.call_iv > 0
        ]
        put_points = [
            (float(s.strike_price), float(s.put_iv) * 100.0)
            for s in strikes if s.put_iv is not None and s.put_iv > 0
        ]
        for x, y in call_points:
            self._call_series.append(x, y)
        for x, y in put_points:
            self._put_series.append(x, y)

        all_points = call_points + put_points
        if not all_points:
            return
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        self._x_axis.setRange(min(xs), max(xs))
        pad = max((max(ys) - min(ys)) * 0.1, 1.0)
        self._y_axis.setRange(min(ys) - pad, max(ys) + pad)

    def clear(self) -> None:
        """Clear the chart."""
        self._call_series.clear()
        self._put_series.clear()
