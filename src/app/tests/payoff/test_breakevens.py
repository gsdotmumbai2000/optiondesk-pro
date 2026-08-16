"""Tests for find_breakevens(): zero-crossing detection with linear
interpolation between payoff curve points."""

from decimal import Decimal

from app.payoff.analytics.breakevens import find_breakevens
from app.payoff.models.result import PayoffCurve, PayoffCurvePoint


def _curve(*price_pnl_pairs: tuple[str, str]) -> PayoffCurve:
    return PayoffCurve(
        points=tuple(
            PayoffCurvePoint(underlying_price=Decimal(p), pnl=Decimal(v)) for p, v in price_pnl_pairs
        )
    )


class TestSingleCrossing:
    def test_interpolates_breakeven_between_two_points(self) -> None:
        """PnL goes from -10 at price 90 to +10 at price 100 -> breakeven at
        the midpoint, 95 (linear interpolation, symmetric crossing)."""
        curve = _curve(("90", "-10"), ("100", "10"))

        breakevens = find_breakevens(curve)

        assert breakevens == (Decimal("95"),)

    def test_interpolates_asymmetric_crossing_correctly(self) -> None:
        """PnL goes from -30 at 90 to +10 at 100 (span 10, ratio 30/40=0.75)
        -> breakeven at 90 + 10*0.75 = 97.5."""
        curve = _curve(("90", "-30"), ("100", "10"))

        breakevens = find_breakevens(curve)

        assert breakevens == (Decimal("97.5"),)


class TestExactZeroPoints:
    def test_exact_zero_at_first_point_is_included(self) -> None:
        curve = _curve(("90", "0"), ("100", "10"))

        assert find_breakevens(curve) == (Decimal("90"),)

    def test_exact_zero_at_last_point_is_included(self) -> None:
        curve = _curve(("90", "-10"), ("100", "0"))

        assert find_breakevens(curve) == (Decimal("100"),)


class TestMultipleCrossings:
    def test_iron_condor_shaped_curve_finds_two_breakevens(self) -> None:
        """Profit zone in the middle, losses on both wings -- the classic
        iron condor payoff shape has exactly two breakevens."""
        curve = _curve(
            ("80", "-10"), ("90", "10"), ("100", "10"), ("110", "10"), ("120", "-10"),
        )

        breakevens = find_breakevens(curve)

        assert len(breakevens) == 2
        assert Decimal("85") <= breakevens[0] <= Decimal("90")
        assert Decimal("110") <= breakevens[1] <= Decimal("115")


class TestNoCrossings:
    def test_all_positive_pnl_has_no_breakevens(self) -> None:
        curve = _curve(("90", "10"), ("100", "20"), ("110", "30"))

        assert find_breakevens(curve) == ()

    def test_all_negative_pnl_has_no_breakevens(self) -> None:
        curve = _curve(("90", "-10"), ("100", "-20"), ("110", "-30"))

        assert find_breakevens(curve) == ()

    def test_fewer_than_two_points_returns_empty(self) -> None:
        assert find_breakevens(_curve()) == ()
        assert find_breakevens(_curve(("100", "0"))) == ()
