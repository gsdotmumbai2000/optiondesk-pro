"""Real payoff diagram chart (strategy P&L vs underlying price).

Renders two curves -- "today" (Black-Scholes time-decayed, smooth) and
"expiry" (intrinsic-only, straight/kinked) -- both color-segmented green
inside the expiry breakeven range and red outside it, plus a hover tooltip,
current-price marker, +/-1SD/2SD lines, loss-zone shading, and drag-to-zoom.
"""

from decimal import Decimal

from PySide6.QtCharts import (QAreaSeries, QChart, QChartView, QLineSeries,
                              QScatterSeries, QSplineSeries, QValueAxis)
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget

from app.payoff.models.result import PayoffCurvePoint, PayoffResult
from app.ui.charts import theme
from app.volatility.models.volatility_result import VolatilityResult


def _interpolate_pnl(points: tuple[PayoffCurvePoint, ...], price: Decimal) -> Decimal:
    """Return the curve's PnL at price, linearly interpolating between samples."""
    if not points:
        return Decimal("0")
    if price <= points[0].underlying_price:
        return points[0].pnl
    if price >= points[-1].underlying_price:
        return points[-1].pnl
    for left, right in zip(points, points[1:]):
        if left.underlying_price <= price <= right.underlying_price:
            span = right.underlying_price - left.underlying_price
            if span == 0:
                return left.pnl
            ratio = (price - left.underlying_price) / span
            return left.pnl + (right.pnl - left.pnl) * ratio
    return points[-1].pnl


def _color_boundaries(
    expiry_points: tuple[PayoffCurvePoint, ...], breakevens: tuple[Decimal, ...]
) -> list[Decimal]:
    """Return sorted price boundaries (range ends + in-range breakevens)."""
    if not expiry_points:
        return []
    low = expiry_points[0].underlying_price
    high = expiry_points[-1].underlying_price
    interior = {b for b in breakevens if low < b < high}
    return sorted({low, high} | interior)


def _build_segments(
    points: tuple[PayoffCurvePoint, ...],
    expiry_points: tuple[PayoffCurvePoint, ...],
    boundaries: list[Decimal],
) -> list[tuple[bool, list[tuple[Decimal, Decimal]]]]:
    """Split points into (is_profit, [(price, pnl), ...]) runs at boundaries.

    Color for each run is decided from the expiry curve's sign at the run's
    midpoint, so both the today and expiry lines share one color boundary
    (the expiry breakevens) regardless of which curve is being segmented --
    this also makes 0/1/2+ breakeven strategies "just work" without special
    casing which side is green.
    """
    segments: list[tuple[bool, list[tuple[Decimal, Decimal]]]] = []
    for left, right in zip(boundaries, boundaries[1:]):
        run: list[tuple[Decimal, Decimal]] = [(left, _interpolate_pnl(points, left))]
        for point in points:
            if left < point.underlying_price < right:
                run.append((point.underlying_price, point.pnl))
        run.append((right, _interpolate_pnl(points, right)))
        midpoint = (left + right) / 2
        is_profit = _interpolate_pnl(expiry_points, midpoint) >= 0
        segments.append((is_profit, run))
    return segments


class _HoverTooltip(QLabel):
    """Floating tooltip shown near the cursor while hovering the chart."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            "background-color: rgba(22, 27, 34, 235);"
            "color: #e6edf3; border: 1px solid #30363d; border-radius: 6px;"
            "padding: 6px 10px; font-size: 11px;"
        )
        self.setTextFormat(Qt.TextFormat.RichText)
        self.hide()


class PayoffChartWidget(QChartView):
    """Sensibull-style payoff diagram: today + expiry curves, breakeven
    coloring, hover P&L tooltip, SD/current-price markers, drag-to-zoom."""

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
        self.setRubberBand(QChartView.RubberBand.RectangleRubberBand)
        self.setMouseTracking(True)

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

        self._zero_series = self._new_line_series(theme.MUTED_TEXT, Qt.PenStyle.DashLine, width=1)

        self._loss_area_lower = QLineSeries()
        self._loss_area_zero = QLineSeries()
        loss_color = QColor(theme.LOSS)
        loss_color.setAlpha(60)
        self._loss_area = QAreaSeries(self._loss_area_lower, self._loss_area_zero)
        self._loss_area.setPen(QPen(Qt.PenStyle.NoPen))
        self._loss_area.setBrush(QBrush(loss_color))
        chart.addSeries(self._loss_area)
        self._loss_area.attachAxis(self._x_axis)
        self._loss_area.attachAxis(self._y_axis)

        self._current_price_series = self._new_line_series(theme.ACCENT, Qt.PenStyle.SolidLine, width=1)

        self._hover_guide = self._new_line_series(theme.MUTED_TEXT, Qt.PenStyle.DashLine, width=1)
        self._hover_marker = QScatterSeries()
        self._hover_marker.setMarkerSize(9)
        self._hover_marker.setColor(theme.TEXT)
        chart.addSeries(self._hover_marker)
        self._hover_marker.attachAxis(self._x_axis)
        self._hover_marker.attachAxis(self._y_axis)

        self._tooltip = _HoverTooltip(self)

        self._today_segments: list[QSplineSeries] = []
        self._expiry_segments: list[QLineSeries] = []
        self._sd_series: list[QLineSeries] = []

        self._today_points: tuple[PayoffCurvePoint, ...] = ()
        self._expiry_points: tuple[PayoffCurvePoint, ...] = ()
        self._spot_price: Decimal | None = None
        self._result_date_label = ""

    def _new_line_series(self, color: QColor, style: Qt.PenStyle, *, width: int) -> QLineSeries:
        series = QLineSeries()
        series.setPen(QPen(color, width, style))
        self.chart().addSeries(series)
        series.attachAxis(self._x_axis)
        series.attachAxis(self._y_axis)
        return series

    def set_result(
        self,
        result: PayoffResult,
        volatility: VolatilityResult | None,
        spot_price: Decimal | None,
    ) -> None:
        """Render today + expiry curves, breakeven coloring, and markers."""
        self._clear_dynamic_series()
        self._today_points = result.today_curve.points
        self._expiry_points = result.payoff_curve.points
        self._spot_price = spot_price
        self._result_date_label = (
            result.calculation_timestamp.strftime("%a, %d %b") if result.calculation_timestamp else ""
        )

        if not self._expiry_points:
            self._reset_persistent_series()
            self._hide_hover()
            return

        boundaries = _color_boundaries(self._expiry_points, result.breakevens)
        self._render_curve(self._today_points, self._expiry_points, boundaries, spline=True)
        self._render_curve(self._expiry_points, self._expiry_points, boundaries, spline=False)

        prices = [point.underlying_price for point in self._expiry_points]
        low, high = min(prices), max(prices)
        self._zero_series.clear()
        self._zero_series.append(float(low), 0.0)
        self._zero_series.append(float(high), 0.0)

        self._render_loss_area(self._expiry_points)
        self._render_current_price(spot_price)
        self._render_sd_lines(volatility, spot_price, low, high)
        self._rescale_axes(low, high)
        self._hide_hover()

    def _render_curve(
        self,
        points: tuple[PayoffCurvePoint, ...],
        expiry_points: tuple[PayoffCurvePoint, ...],
        boundaries: list[Decimal],
        *,
        spline: bool,
    ) -> None:
        if not points or len(boundaries) < 2:
            return
        chart = self.chart()
        for is_profit, run in _build_segments(points, expiry_points, boundaries):
            series = QSplineSeries() if spline else QLineSeries()
            color = theme.PROFIT if is_profit else theme.LOSS
            series.setPen(QPen(color, 2))
            for price, pnl in run:
                series.append(float(price), float(pnl))
            chart.addSeries(series)
            series.attachAxis(self._x_axis)
            series.attachAxis(self._y_axis)
            if spline:
                self._today_segments.append(series)
            else:
                self._expiry_segments.append(series)

    def _render_loss_area(self, expiry_points: tuple[PayoffCurvePoint, ...]) -> None:
        self._loss_area_lower.clear()
        self._loss_area_zero.clear()
        for point in expiry_points:
            price = float(point.underlying_price)
            self._loss_area_lower.append(price, min(float(point.pnl), 0.0))
            self._loss_area_zero.append(price, 0.0)

    def _render_current_price(self, spot_price: Decimal | None) -> None:
        self._current_price_series.clear()
        if spot_price is None or not self._expiry_points:
            return
        pnls = [point.pnl for point in self._today_points + self._expiry_points] or [Decimal("0")]
        y_min, y_max = min(pnls + [Decimal("0")]), max(pnls + [Decimal("0")])
        self._current_price_series.append(float(spot_price), float(y_min))
        self._current_price_series.append(float(spot_price), float(y_max))

    def _render_sd_lines(
        self,
        volatility: VolatilityResult | None,
        spot_price: Decimal | None,
        low: Decimal,
        high: Decimal,
    ) -> None:
        if volatility is None or spot_price is None:
            return
        move = volatility.expected_move.to_expiry
        if move <= 0:
            return
        pnls = [point.pnl for point in self._today_points + self._expiry_points] or [Decimal("0")]
        y_min, y_max = min(pnls + [Decimal("0")]), max(pnls + [Decimal("0")])
        for multiple in (Decimal("1"), Decimal("2")):
            for direction in (Decimal("1"), Decimal("-1")):
                price = spot_price + direction * multiple * move
                if price < low or price > high:
                    continue
                series = self._new_line_series(theme.MUTED_TEXT, Qt.PenStyle.DotLine, width=1)
                series.append(float(price), float(y_min))
                series.append(float(price), float(y_max))
                self._sd_series.append(series)

    def _rescale_axes(self, low: Decimal, high: Decimal) -> None:
        self._x_axis.setRange(float(low), float(high))
        pnls = [point.pnl for point in self._today_points + self._expiry_points]
        y_min, y_max = min(pnls + [Decimal("0")]), max(pnls + [Decimal("0")])
        pad = max((y_max - y_min) * Decimal("0.1"), Decimal("1"))
        self._y_axis.setRange(float(y_min - pad), float(y_max + pad))

    def _clear_dynamic_series(self) -> None:
        chart = self.chart()
        for series in self._today_segments + self._expiry_segments + self._sd_series:
            chart.removeSeries(series)
        self._today_segments = []
        self._expiry_segments = []
        self._sd_series = []

    def _reset_persistent_series(self) -> None:
        self._zero_series.clear()
        self._loss_area_lower.clear()
        self._loss_area_zero.clear()
        self._current_price_series.clear()

    def clear(self) -> None:
        """Clear the chart (e.g. when no strategy is active)."""
        self._clear_dynamic_series()
        self._reset_persistent_series()
        self._today_points = ()
        self._expiry_points = ()
        self._spot_price = None
        self._hide_hover()

    # --- Hover interaction ---

    def mouseMoveEvent(self, event) -> None:
        """Track cursor across the plot area and show today/expiry P&L."""
        super().mouseMoveEvent(event)
        if not self._today_points or not self._expiry_points:
            return
        scene_pos = self.mapToScene(event.position().toPoint())
        chart_pos = self.chart().mapFromScene(scene_pos)
        value = self.chart().mapToValue(chart_pos)
        low = self._expiry_points[0].underlying_price
        high = self._expiry_points[-1].underlying_price
        price = Decimal(str(round(value.x(), 2)))
        if price < low or price > high:
            self._hide_hover()
            return
        today_pnl = _interpolate_pnl(self._today_points, price)
        expiry_pnl = _interpolate_pnl(self._expiry_points, price)
        self._update_hover(price, today_pnl, expiry_pnl, chart_pos)

    def leaveEvent(self, event) -> None:
        """Hide the hover tooltip/guide/marker when the cursor leaves."""
        super().leaveEvent(event)
        self._hide_hover()

    def _update_hover(
        self, price: Decimal, today_pnl: Decimal, expiry_pnl: Decimal, chart_pos: QPointF
    ) -> None:
        y_min, y_max = self._y_axis.min(), self._y_axis.max()
        self._hover_guide.clear()
        self._hover_guide.append(float(price), y_min)
        self._hover_guide.append(float(price), y_max)
        self._hover_marker.clear()
        self._hover_marker.append(float(price), float(today_pnl))

        change_pct = Decimal("0")
        if self._spot_price:
            change_pct = (price - self._spot_price) / self._spot_price * 100

        self._tooltip.setText(
            "<div>When price is at</div>"
            f"<div style='font-size:14px;font-weight:bold;'>{price:,.2f} "
            f"<span style='color:{'#3fb950' if change_pct >= 0 else '#f85149'};'>"
            f"({change_pct:+.1f}%)</span></div>"
            "<div style='margin-top:4px;color:#8b949e;'>Expected P&amp;L on "
            f"{self._result_date_label}</div>"
            f"<div style='color:{'#3fb950' if today_pnl >= 0 else '#f85149'};font-weight:bold;'>"
            f"{today_pnl:+,.0f}</div>"
            "<div style='margin-top:4px;color:#8b949e;'>Expiry date</div>"
            f"<div style='color:{'#3fb950' if expiry_pnl >= 0 else '#f85149'};font-weight:bold;'>"
            f"{expiry_pnl:+,.0f}</div>"
        )
        self._tooltip.adjustSize()
        pos = self.chart().mapToPosition(chart_pos)
        x = min(max(int(pos.x()) + 12, 0), max(self.width() - self._tooltip.width(), 0))
        y = min(max(int(pos.y()) - self._tooltip.height() - 12, 0), max(self.height() - self._tooltip.height(), 0))
        self._tooltip.move(x, y)
        self._tooltip.show()

    def _hide_hover(self) -> None:
        self._hover_guide.clear()
        self._hover_marker.clear()
        self._tooltip.hide()
