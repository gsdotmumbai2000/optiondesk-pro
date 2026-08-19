"""Real live price candlestick chart, rendering OHLC bars aggregated by
TickCandleBuffer from the live tick stream."""

from datetime import datetime

from PySide6.QtCharts import QCandlestickSeries, QCandlestickSet, QChart, QChartView, QDateTimeAxis, QValueAxis
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.ui.charts import theme
from app.ui.market.tick_candle_buffer import Candle


class PriceChartWidget(QChartView):
    """Live OHLC candlestick chart."""

    def __init__(self, title: str = "Price Chart", parent: QWidget | None = None) -> None:
        """Initialize an empty price chart."""
        chart = QChart()
        chart.setTitle(title)
        chart.legend().setVisible(False)
        chart.setBackgroundBrush(theme.BACKGROUND)
        chart.setTitleBrush(theme.TEXT)
        super().__init__(chart, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._series = QCandlestickSeries()
        self._series.setIncreasingColor(theme.PROFIT)
        self._series.setDecreasingColor(theme.LOSS)
        self._series.setBodyOutlineVisible(False)
        chart.addSeries(self._series)

        self._x_axis = QDateTimeAxis()
        self._x_axis.setTitleText("Time")
        self._x_axis.setLabelsColor(theme.MUTED_TEXT)
        self._x_axis.setTitleBrush(theme.MUTED_TEXT)
        self._x_axis.setGridLineColor(theme.BORDER)
        self._x_axis.setFormat("HH:mm")
        self._y_axis = QValueAxis()
        self._y_axis.setTitleText("Price")
        self._y_axis.setLabelsColor(theme.MUTED_TEXT)
        self._y_axis.setTitleBrush(theme.MUTED_TEXT)
        self._y_axis.setGridLineColor(theme.BORDER)
        chart.addAxis(self._x_axis, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(self._y_axis, Qt.AlignmentFlag.AlignLeft)
        self._series.attachAxis(self._x_axis)
        self._series.attachAxis(self._y_axis)

    def set_candles(self, candles: tuple[Candle, ...]) -> None:
        """Render the given OHLC candles. Clears the chart when empty."""
        self._series.clear()
        if not candles:
            return
        timestamps_ms = []
        for candle in candles:
            ts_ms = int(candle.start.timestamp() * 1000)
            timestamps_ms.append(ts_ms)
            self._series.append(
                QCandlestickSet(
                    float(candle.open), float(candle.high), float(candle.low), float(candle.close), ts_ms,
                )
            )

        tzinfo = candles[0].start.tzinfo
        self._x_axis.setRange(
            datetime.fromtimestamp(min(timestamps_ms) / 1000, tz=tzinfo),
            datetime.fromtimestamp(max(timestamps_ms) / 1000, tz=tzinfo),
        )
        lows = [float(c.low) for c in candles]
        highs = [float(c.high) for c in candles]
        y_min, y_max = min(lows), max(highs)
        pad = max((y_max - y_min) * 0.1, 1.0)
        self._y_axis.setRange(y_min - pad, y_max + pad)

    def clear(self) -> None:
        """Clear the chart."""
        self._series.clear()
