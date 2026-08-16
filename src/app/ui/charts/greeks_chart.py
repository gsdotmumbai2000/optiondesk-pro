"""Real Greeks bar chart (current delta/gamma/theta/vega/rho snapshot)."""

from PySide6.QtCharts import (
    QAbstractBarSeries,
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QValueAxis,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.greeks.models.greeks_result import GreeksResult
from app.ui.charts import theme

_LABELS = ("Delta", "Gamma", "Theta", "Vega", "Rho")


class GreeksChartWidget(QChartView):
    """Bar chart of the primary Greeks for the current position/strategy."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize an empty Greeks chart."""
        chart = QChart()
        chart.setTitle("Greeks")
        chart.legend().setVisible(False)
        chart.setBackgroundBrush(theme.BACKGROUND)
        chart.setTitleBrush(theme.TEXT)
        super().__init__(chart, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._bar_set = QBarSet("Greeks")
        self._bar_set.setColor(theme.ACCENT)
        self._bar_set.setLabelColor(theme.TEXT)
        self._series = QBarSeries()
        self._series.append(self._bar_set)
        # Delta/gamma and theta/vega/rho sit on wildly different natural
        # scales (e.g. delta ~0-1 vs vega ~0-20), so a small bar can be
        # visually invisible next to a large one on the same axis --
        # printed value labels keep every bar's number readable regardless
        # of its rendered height.
        self._series.setLabelsVisible(True)
        self._series.setLabelsPosition(QAbstractBarSeries.LabelsPosition.LabelsOutsideEnd)
        self._series.setLabelsPrecision(4)
        chart.addSeries(self._series)

        self._x_axis = QBarCategoryAxis()
        self._x_axis.append(list(_LABELS))
        self._x_axis.setLabelsColor(theme.MUTED_TEXT)
        self._y_axis = QValueAxis()
        self._y_axis.setLabelsColor(theme.MUTED_TEXT)
        self._y_axis.setGridLineColor(theme.BORDER)
        chart.addAxis(self._x_axis, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(self._y_axis, Qt.AlignmentFlag.AlignLeft)
        self._series.attachAxis(self._x_axis)
        self._series.attachAxis(self._y_axis)
        self._set_values([0.0] * 5)

    def set_greeks(self, greeks: GreeksResult) -> None:
        """Render a Greeks snapshot as bars."""
        values = [
            float(greeks.delta), float(greeks.gamma), float(greeks.theta),
            float(greeks.vega), float(greeks.rho),
        ]
        self._set_values(values)

    def clear(self) -> None:
        """Reset all bars to zero."""
        self._set_values([0.0] * 5)

    def _set_values(self, values: list[float]) -> None:
        while self._bar_set.count():
            self._bar_set.remove(0)
        for value in values:
            self._bar_set.append(value)
        y_min, y_max = min(values + [0.0]), max(values + [0.0])
        pad = max((y_max - y_min) * 0.15, 0.1)
        self._y_axis.setRange(y_min - pad, y_max + pad)
