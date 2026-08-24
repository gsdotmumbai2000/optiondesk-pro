"""Tests for the real chart widgets (payoff, PnL, volatility, Greeks).
Chart correctness is structural, not pixel-based: series point counts,
axis ranges, and clear() behavior -- rendering pixels is verified
separately via a visual screenshot check, not asserted in these tests.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from PySide6.QtWidgets import QApplication

from app.calculation.models.snapshots import OptionChainSnapshot, OptionStrikeSnapshot
from app.greeks.models.greeks_result import GreeksResult
from app.payoff.models.enums import PayoffModelVersion
from app.payoff.models.result import (PayoffCurve, PayoffCurvePoint, PayoffResult,
                                      PayoffRiskTable)
from app.ui.charts import theme
from app.ui.charts.greeks_chart import GreeksChartWidget
from app.ui.charts.payoff_chart import PayoffChartWidget
from app.ui.charts.pnl_chart import PnlChartWidget
from app.ui.charts.price_chart import PriceChartWidget
from app.ui.charts.volatility_chart import VolatilityChartWidget
from app.ui.market.tick_candle_buffer import Candle
from app.volatility.models.enums import VolatilityModelVersion
from app.volatility.models.volatility_result import (ExpectedMove, HistoricalVolatility,
                                                      VolatilityResult)


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _curve(*price_pnl_pairs: tuple[str, str]) -> PayoffCurve:
    return PayoffCurve(
        points=tuple(
            PayoffCurvePoint(underlying_price=Decimal(p), pnl=Decimal(v)) for p, v in price_pnl_pairs
        )
    )


def _result(
    expiry: PayoffCurve,
    today: PayoffCurve | None = None,
    breakevens: tuple[Decimal, ...] = (),
) -> PayoffResult:
    return PayoffResult(
        current_pnl=Decimal("0"), expiry_pnl=Decimal("0"), future_value=Decimal("0"),
        maximum_gain=None, maximum_loss=None, risk_reward_ratio=None,
        breakevens=breakevens, payoff_curve=expiry, risk_table=PayoffRiskTable(),
        probability_weighted_pnl=None, calculation_timestamp=datetime(2026, 8, 22, tzinfo=timezone.utc),
        model_version=PayoffModelVersion.V1, today_curve=today if today is not None else expiry,
    )


def _volatility(move_to_expiry: str) -> VolatilityResult:
    return VolatilityResult(
        implied_volatility=Decimal("0.15"), annualized_volatility=Decimal("0.15"),
        realized_volatility=Decimal("0.14"),
        historical_volatility=HistoricalVolatility(primary=Decimal("0.14")),
        expected_move=ExpectedMove(to_expiry=Decimal(move_to_expiry)),
        iv_percentile=Decimal("50"), calculation_timestamp=datetime(2026, 8, 22, tzinfo=timezone.utc),
        model_version=VolatilityModelVersion.V1,
    )


class TestPayoffChartWidget:
    def test_single_breakeven_produces_two_colored_segments_per_curve(self, qapp: QApplication) -> None:
        """One breakeven at 103 splits [90,120] into a loss run [90,103]
        and a profit run [103,120] for both today and expiry curves."""
        expiry = _curve(("90", "-300"), ("100", "-100"), ("110", "700"), ("120", "700"))
        widget = PayoffChartWidget()

        widget.set_result(_result(expiry, breakevens=(Decimal("103"),)), None, Decimal("105"))

        assert len(widget._today_segments) == 2
        assert len(widget._expiry_segments) == 2

    def test_segment_colors_match_expiry_sign_on_each_side(self, qapp: QApplication) -> None:
        expiry = _curve(("90", "-300"), ("100", "-100"), ("110", "700"), ("120", "700"))
        widget = PayoffChartWidget()

        widget.set_result(_result(expiry, breakevens=(Decimal("103"),)), None, Decimal("105"))

        loss_segment, profit_segment = widget._expiry_segments
        assert loss_segment.pen().color().name() == theme.LOSS.name()
        assert profit_segment.pen().color().name() == theme.PROFIT.name()

    def test_no_breakevens_produces_a_single_segment(self, qapp: QApplication) -> None:
        """An all-profit (or all-loss) curve with zero crossings is one run."""
        expiry = _curve(("90", "10"), ("100", "20"), ("120", "30"))
        widget = PayoffChartWidget()

        widget.set_result(_result(expiry), None, Decimal("100"))

        assert len(widget._expiry_segments) == 1
        assert widget._expiry_segments[0].pen().color().name() == theme.PROFIT.name()

    def test_zero_reference_line_spans_full_price_range(self, qapp: QApplication) -> None:
        expiry = _curve(("100", "-10"), ("120", "10"))
        widget = PayoffChartWidget()

        widget.set_result(_result(expiry, breakevens=(Decimal("110"),)), None, None)

        assert widget._zero_series.count() == 2
        points = [widget._zero_series.at(i) for i in range(2)]
        assert {p.x() for p in points} == {100.0, 120.0}
        assert all(p.y() == 0.0 for p in points)

    def test_x_axis_range_matches_price_bounds(self, qapp: QApplication) -> None:
        expiry = _curve(("90", "-5"), ("100", "0"), ("130", "20"))
        widget = PayoffChartWidget()

        widget.set_result(_result(expiry, breakevens=(Decimal("100"),)), None, None)

        assert widget._x_axis.min() == 90.0
        assert widget._x_axis.max() == 130.0

    def test_loss_area_lower_series_clips_profit_to_zero(self, qapp: QApplication) -> None:
        expiry = _curve(("90", "-300"), ("100", "-100"), ("110", "700"), ("120", "700"))
        widget = PayoffChartWidget()

        widget.set_result(_result(expiry, breakevens=(Decimal("103"),)), None, None)

        values = {widget._loss_area_lower.at(i).x(): widget._loss_area_lower.at(i).y() for i in range(4)}
        assert values[90.0] == -300.0
        assert values[110.0] == 0.0  # profitable point clipped to 0, not 700

    def test_current_price_marker_present_when_spot_given(self, qapp: QApplication) -> None:
        expiry = _curve(("90", "-10"), ("120", "10"))
        widget = PayoffChartWidget()

        widget.set_result(_result(expiry, breakevens=(Decimal("105"),)), None, Decimal("105"))

        assert widget._current_price_series.count() == 2
        assert all(widget._current_price_series.at(i).x() == 105.0 for i in range(2))

    def test_current_price_marker_absent_when_spot_missing(self, qapp: QApplication) -> None:
        expiry = _curve(("90", "-10"), ("120", "10"))
        widget = PayoffChartWidget()

        widget.set_result(_result(expiry, breakevens=(Decimal("105"),)), None, None)

        assert widget._current_price_series.count() == 0

    def test_sd_lines_rendered_when_volatility_present(self, qapp: QApplication) -> None:
        expiry = _curve(("80", "-10"), ("100", "0"), ("120", "10"))
        widget = PayoffChartWidget()

        widget.set_result(
            _result(expiry, breakevens=(Decimal("100"),)), _volatility("5"), Decimal("100")
        )

        # +/-1SD (95, 105) and +/-2SD (90, 110) all fall within [80, 120]
        assert len(widget._sd_series) == 4

    def test_sd_lines_absent_without_volatility(self, qapp: QApplication) -> None:
        expiry = _curve(("80", "-10"), ("100", "0"), ("120", "10"))
        widget = PayoffChartWidget()

        widget.set_result(_result(expiry, breakevens=(Decimal("100"),)), None, Decimal("100"))

        assert widget._sd_series == []

    def test_empty_curve_clears_series(self, qapp: QApplication) -> None:
        expiry = _curve(("100", "5"))
        widget = PayoffChartWidget()
        widget.set_result(_result(expiry), None, Decimal("100"))

        widget.set_result(_result(PayoffCurve()), None, None)

        assert widget._today_segments == []
        assert widget._expiry_segments == []
        assert widget._zero_series.count() == 0

    def test_clear_resets_everything(self, qapp: QApplication) -> None:
        expiry = _curve(("90", "-10"), ("120", "10"))
        widget = PayoffChartWidget()
        widget.set_result(_result(expiry, breakevens=(Decimal("105"),)), None, Decimal("105"))

        widget.clear()

        assert widget._today_segments == []
        assert widget._expiry_segments == []
        assert widget._zero_series.count() == 0
        assert widget._current_price_series.count() == 0

    def test_repeated_set_result_does_not_leak_series(self, qapp: QApplication) -> None:
        """Regression guard: dynamic series must be removed before rebuilding,
        not just dropped, or repeated evaluates would accumulate stale series."""
        expiry = _curve(("90", "-300"), ("100", "-100"), ("110", "700"), ("120", "700"))
        widget = PayoffChartWidget()

        for _ in range(3):
            widget.set_result(_result(expiry, breakevens=(Decimal("103"),)), None, Decimal("105"))

        assert len(widget._today_segments) == 2
        assert len(widget._expiry_segments) == 2
        assert len(widget.chart().series()) == len(
            widget._today_segments
        ) + len(widget._expiry_segments) + 5  # zero, loss area, current price, hover guide, hover marker

    def test_hover_reports_interpolated_today_and_expiry_pnl(self, qapp: QApplication) -> None:
        expiry = _curve(("90", "-100"), ("100", "0"), ("110", "700"))
        today = _curve(("90", "-80"), ("100", "20"), ("110", "650"))
        widget = PayoffChartWidget()
        widget.set_result(_result(expiry, today, breakevens=(Decimal("100"),)), None, Decimal("100"))

        from PySide6.QtCore import QPointF
        widget._update_hover(Decimal("95"), Decimal("-30"), Decimal("-50"), QPointF(50, 50))

        assert widget._hover_marker.count() == 1
        assert widget._hover_marker.at(0).x() == 95.0
        assert "95.00" in widget._tooltip.text()
        assert "-30" in widget._tooltip.text()
        assert "-50" in widget._tooltip.text()

    def test_leave_event_hides_hover(self, qapp: QApplication) -> None:
        expiry = _curve(("90", "-10"), ("120", "10"))
        widget = PayoffChartWidget()
        widget.set_result(_result(expiry, breakevens=(Decimal("105"),)), None, Decimal("105"))
        from PySide6.QtCore import QPointF
        widget._update_hover(Decimal("100"), Decimal("-5"), Decimal("-5"), QPointF(10, 10))

        widget._hide_hover()

        assert widget._hover_marker.count() == 0
        assert widget._hover_guide.count() == 0


class TestPnlChartWidget:
    def test_set_series_populates_all_points(self, qapp: QApplication) -> None:
        widget = PnlChartWidget()
        points = [
            (datetime(2026, 8, 14, tzinfo=timezone.utc), Decimal("100000")),
            (datetime(2026, 8, 15, tzinfo=timezone.utc), Decimal("101000")),
        ]

        widget.set_series(points)

        assert widget._series.count() == 2

    def test_y_axis_range_matches_value_bounds_with_padding(self, qapp: QApplication) -> None:
        widget = PnlChartWidget()
        points = [
            (datetime(2026, 8, 14, tzinfo=timezone.utc), Decimal("100")),
            (datetime(2026, 8, 15, tzinfo=timezone.utc), Decimal("200")),
        ]

        widget.set_series(points)

        assert widget._y_axis.min() < 100.0
        assert widget._y_axis.max() > 200.0

    def test_empty_series_clears_chart(self, qapp: QApplication) -> None:
        widget = PnlChartWidget()
        widget.set_series([(datetime(2026, 8, 14, tzinfo=timezone.utc), Decimal("1"))])

        widget.set_series([])

        assert widget._series.count() == 0

    def test_custom_title_is_applied(self, qapp: QApplication) -> None:
        widget = PnlChartWidget(title="Equity Curve")

        assert widget.chart().title() == "Equity Curve"


class TestVolatilityChartWidget:
    def _chain(self, *strikes: OptionStrikeSnapshot) -> OptionChainSnapshot:
        return OptionChainSnapshot(
            underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026",
            spot_price=Decimal("24500"), atm_strike=Decimal("24500"), strikes=strikes,
        )

    def test_set_chain_populates_call_and_put_series_separately(self, qapp: QApplication) -> None:
        widget = VolatilityChartWidget()
        chain = self._chain(
            OptionStrikeSnapshot(strike_price=Decimal("24400"), call_iv=Decimal("0.18"), put_iv=Decimal("0.22")),
            OptionStrikeSnapshot(strike_price=Decimal("24600"), call_iv=Decimal("0.16"), put_iv=Decimal("0.25")),
        )

        widget.set_chain(chain)

        assert widget._call_series.count() == 2
        assert widget._put_series.count() == 2

    def test_iv_values_are_scaled_to_percent(self, qapp: QApplication) -> None:
        widget = VolatilityChartWidget()
        chain = self._chain(OptionStrikeSnapshot(strike_price=Decimal("24500"), call_iv=Decimal("0.20")))

        widget.set_chain(chain)

        point = widget._call_series.at(0)
        assert point.y() == pytest.approx(20.0)

    def test_strikes_missing_one_side_only_populate_that_series(self, qapp: QApplication) -> None:
        widget = VolatilityChartWidget()
        chain = self._chain(OptionStrikeSnapshot(strike_price=Decimal("24500"), call_iv=Decimal("0.18")))

        widget.set_chain(chain)

        assert widget._call_series.count() == 1
        assert widget._put_series.count() == 0

    def test_empty_chain_clears_both_series(self, qapp: QApplication) -> None:
        widget = VolatilityChartWidget()
        widget.set_chain(self._chain(OptionStrikeSnapshot(strike_price=Decimal("24500"), call_iv=Decimal("0.18"))))

        widget.set_chain(self._chain())

        assert widget._call_series.count() == 0
        assert widget._put_series.count() == 0


class TestPriceChartWidget:
    def _candle(self, minute: int, open_: str, high: str, low: str, close: str) -> Candle:
        return Candle(
            start=datetime(2026, 8, 19, 9, 15 + minute, tzinfo=timezone.utc),
            open=Decimal(open_), high=Decimal(high), low=Decimal(low), close=Decimal(close),
        )

    def test_set_candles_populates_all_sets(self, qapp: QApplication) -> None:
        widget = PriceChartWidget()
        candles = (
            self._candle(0, "100", "105", "98", "102"),
            self._candle(1, "102", "108", "101", "107"),
        )

        widget.set_candles(candles)

        assert len(widget._series.sets()) == 2

    def test_x_axis_range_matches_candle_time_bounds(self, qapp: QApplication) -> None:
        widget = PriceChartWidget()
        candles = (
            self._candle(0, "100", "105", "98", "102"),
            self._candle(5, "102", "108", "101", "107"),
        )

        widget.set_candles(candles)

        assert widget._x_axis.min() == candles[0].start
        assert widget._x_axis.max() == candles[1].start

    def test_y_axis_range_covers_low_to_high_with_padding(self, qapp: QApplication) -> None:
        widget = PriceChartWidget()
        candles = (self._candle(0, "100", "110", "90", "105"),)

        widget.set_candles(candles)

        assert widget._y_axis.min() < 90.0
        assert widget._y_axis.max() > 110.0

    def test_empty_candles_clears_series(self, qapp: QApplication) -> None:
        widget = PriceChartWidget()
        widget.set_candles((self._candle(0, "100", "105", "98", "102"),))

        widget.set_candles(())

        assert len(widget._series.sets()) == 0

    def test_clear_resets_series(self, qapp: QApplication) -> None:
        widget = PriceChartWidget()
        widget.set_candles((self._candle(0, "100", "105", "98", "102"),))

        widget.clear()

        assert len(widget._series.sets()) == 0


class TestGreeksChartWidget:
    def _greeks(self) -> GreeksResult:
        return GreeksResult(
            delta=Decimal("0.5"), gamma=Decimal("0.02"), theta=Decimal("-1.5"), vega=Decimal("10"),
            rho=Decimal("3"), vanna=Decimal("0.1"), charm=Decimal("0.05"), vomma=Decimal("0.2"),
            calculation_timestamp=datetime.now(timezone.utc),
        )

    def test_starts_with_five_zero_bars(self, qapp: QApplication) -> None:
        widget = GreeksChartWidget()

        assert widget._bar_set.count() == 5
        assert all(widget._bar_set.at(i) == 0.0 for i in range(5))

    def test_set_greeks_populates_bars_in_delta_gamma_theta_vega_rho_order(self, qapp: QApplication) -> None:
        widget = GreeksChartWidget()

        widget.set_greeks(self._greeks())

        values = [widget._bar_set.at(i) for i in range(5)]
        assert values == [0.5, 0.02, -1.5, 10.0, 3.0]

    def test_clear_resets_bars_to_zero(self, qapp: QApplication) -> None:
        widget = GreeksChartWidget()
        widget.set_greeks(self._greeks())

        widget.clear()

        assert all(widget._bar_set.at(i) == 0.0 for i in range(5))

    def test_bar_count_stays_five_after_multiple_updates(self, qapp: QApplication) -> None:
        """Regression guard: _set_values() clears the QBarSet before
        re-appending, so repeated updates must never accumulate bars."""
        widget = GreeksChartWidget()

        widget.set_greeks(self._greeks())
        widget.set_greeks(self._greeks())
        widget.set_greeks(self._greeks())

        assert widget._bar_set.count() == 5
