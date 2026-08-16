"""Real PnL / equity time-series chart."""

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from PySide6.QtCharts import QChart, QChartView, QDateTimeAxis, QLineSeries, QValueAxis
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.ui.charts import theme


class PnlChartWidget(QChartView):
    """PnL/equity value over time. Used for both portfolio PnL history and
    backtest equity curves -- both are just (timestamp, value) series."""

    def __init__(self, title: str = "PnL", parent: QWidget | None = None) -> None:
        """Initialize an empty PnL chart."""
        chart = QChart()
        chart.setTitle(title)
        chart.legend().setVisible(False)
        chart.setBackgroundBrush(theme.BACKGROUND)
        chart.setTitleBrush(theme.TEXT)
        super().__init__(chart, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._series = QLineSeries()
        self._series.setPen(QPen(theme.ACCENT, 2))
        chart.addSeries(self._series)

        self._x_axis = QDateTimeAxis()
        self._x_axis.setTitleText("Time")
        self._x_axis.setLabelsColor(theme.MUTED_TEXT)
        self._x_axis.setTitleBrush(theme.MUTED_TEXT)
        self._x_axis.setGridLineColor(theme.BORDER)
        self._x_axis.setFormat("dd-MMM HH:mm")
        self._y_axis = QValueAxis()
        self._y_axis.setTitleText("Value")
        self._y_axis.setLabelsColor(theme.MUTED_TEXT)
        self._y_axis.setTitleBrush(theme.MUTED_TEXT)
        self._y_axis.setGridLineColor(theme.BORDER)
        chart.addAxis(self._x_axis, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(self._y_axis, Qt.AlignmentFlag.AlignLeft)
        self._series.attachAxis(self._x_axis)
        self._series.attachAxis(self._y_axis)

    def set_series(self, points: Sequence[tuple[datetime, Decimal]]) -> None:
        """Render a time series. Clears the chart when `points` is empty."""
        self._series.clear()
        if not points:
            return
        timestamps_ms = [int(ts.timestamp() * 1000) for ts, _ in points]
        values = [float(value) for _, value in points]
        for ts_ms, value in zip(timestamps_ms, values):
            self._series.append(float(ts_ms), value)

        self._x_axis.setRange(
            datetime.fromtimestamp(min(timestamps_ms) / 1000, tz=points[0][0].tzinfo),
            datetime.fromtimestamp(max(timestamps_ms) / 1000, tz=points[0][0].tzinfo),
        )
        y_min, y_max = min(values), max(values)
        pad = max((y_max - y_min) * 0.1, 1.0)
        self._y_axis.setRange(y_min - pad, y_max + pad)

    def clear(self) -> None:
        """Clear the chart."""
        self._series.clear()
