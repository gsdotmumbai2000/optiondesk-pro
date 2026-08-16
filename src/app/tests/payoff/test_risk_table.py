"""Tests for build_risk_table() and curve_extrema()."""

from decimal import Decimal

from app.payoff.analytics.risk_table import build_risk_table, curve_extrema
from app.payoff.models.result import PayoffCurve, PayoffCurvePoint


def _curve(*price_pnl_pairs: tuple[str, str]) -> PayoffCurve:
    return PayoffCurve(
        points=tuple(
            PayoffCurvePoint(underlying_price=Decimal(p), pnl=Decimal(v)) for p, v in price_pnl_pairs
        )
    )


class TestCurveExtrema:
    def test_returns_max_and_min_pnl_when_mixed_signs(self) -> None:
        curve = _curve(("90", "-30"), ("100", "5"), ("110", "20"))

        max_gain, max_loss = curve_extrema(curve)

        assert max_gain == Decimal("20")
        assert max_loss == Decimal("-30")

    def test_all_positive_pnl_has_no_max_loss(self) -> None:
        curve = _curve(("90", "5"), ("100", "10"))

        max_gain, max_loss = curve_extrema(curve)

        assert max_gain == Decimal("10")
        assert max_loss is None

    def test_all_negative_pnl_has_no_max_gain(self) -> None:
        curve = _curve(("90", "-5"), ("100", "-10"))

        max_gain, max_loss = curve_extrema(curve)

        assert max_gain is None
        assert max_loss == Decimal("-10")

    def test_empty_curve_returns_none_none(self) -> None:
        assert curve_extrema(_curve()) == (None, None)


class TestBuildRiskTable:
    def test_each_row_has_uniform_probability(self) -> None:
        curve = _curve(("90", "-10"), ("100", "0"), ("110", "10"), ("120", "20"))

        table = build_risk_table(curve)

        assert len(table.rows) == 4
        assert all(row.probability == Decimal("1") / Decimal("4") for row in table.rows)

    def test_rows_preserve_price_and_pnl(self) -> None:
        curve = _curve(("90", "-10"), ("110", "10"))

        table = build_risk_table(curve)

        assert table.rows[0].underlying_price == Decimal("90")
        assert table.rows[0].pnl == Decimal("-10")
        assert table.rows[1].underlying_price == Decimal("110")
        assert table.rows[1].pnl == Decimal("10")

    def test_empty_curve_returns_empty_table(self) -> None:
        table = build_risk_table(_curve())

        assert table.rows == ()
