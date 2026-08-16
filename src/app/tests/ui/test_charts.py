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
from app.payoff.models.result import PayoffCurve, PayoffCurvePoint
from app.ui.charts.greeks_chart import GreeksChartWidget
from app.ui.charts.payoff_chart import PayoffChartWidget
from app.ui.charts.pnl_chart import PnlChartWidget
from app.ui.charts.volatility_chart import VolatilityChartWidget


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


class TestPayoffChartWidget:
    def test_set_curve_populates_pnl_series_with_all_points(self, qapp: QApplication) -> None:
        widget = PayoffChartWidget()
        curve = _curve(("100", "-10"), ("110", "0"), ("120", "10"))

        widget.set_curve(curve)

        assert widget._pnl_series.count() == 3

    def test_zero_reference_line_spans_full_price_range(self, qapp: QApplication) -> None:
        widget = PayoffChartWidget()
        curve = _curve(("100", "-10"), ("120", "10"))

        widget.set_curve(curve)

        assert widget._zero_series.count() == 2
        points = [widget._zero_series.at(i) for i in range(2)]
        assert {p.x() for p in points} == {100.0, 120.0}
        assert all(p.y() == 0.0 for p in points)

    def test_x_axis_range_matches_price_bounds(self, qapp: QApplication) -> None:
        widget = PayoffChartWidget()
        curve = _curve(("90", "-5"), ("100", "0"), ("130", "20"))

        widget.set_curve(curve)

        assert widget._x_axis.min() == 90.0
        assert widget._x_axis.max() == 130.0

    def test_empty_curve_clears_series(self, qapp: QApplication) -> None:
        widget = PayoffChartWidget()
        widget.set_curve(_curve(("100", "5")))

        widget.set_curve(PayoffCurve())

        assert widget._pnl_series.count() == 0
        assert widget._zero_series.count() == 0

    def test_clear_resets_both_series(self, qapp: QApplication) -> None:
        widget = PayoffChartWidget()
        widget.set_curve(_curve(("100", "5")))

        widget.clear()

        assert widget._pnl_series.count() == 0
        assert widget._zero_series.count() == 0


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
