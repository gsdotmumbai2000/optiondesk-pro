"""Tests for aggregate_greeks(): sums reference Greeks across legs,
exactly for legs matching the reference context's strike/expiry, and via a
first-order (gamma-adjusted delta) approximation for legs that don't.
"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.greeks.models.greeks_result import GreeksResult
from app.payoff.models.legs import StrategyLeg
from app.pricing.models.enums import OptionType
from app.risk.analytics.greeks_aggregation import aggregate_greeks


def _context(atm_strike: Decimal, expiry: date) -> SimpleNamespace:
    return SimpleNamespace(atm_strike=atm_strike, expiry=expiry)


def _greeks() -> GreeksResult:
    from datetime import datetime, timezone

    return GreeksResult(
        delta=Decimal("0.5"), gamma=Decimal("0.02"), theta=Decimal("-1.5"), vega=Decimal("10"),
        rho=Decimal("3"), vanna=Decimal("0.1"), charm=Decimal("0.05"), vomma=Decimal("0.2"),
        calculation_timestamp=datetime.now(timezone.utc),
    )


def _leg(quantity: int, strike: Decimal, expiry: date, option_type: OptionType = OptionType.CALL) -> StrategyLeg:
    return StrategyLeg(strike=strike, option_type=option_type, quantity=quantity, premium=Decimal("5"), expiry=expiry)


class TestMatchingLegUsesGreeksDirectly:
    def test_single_matching_leg_scales_by_quantity(self) -> None:
        context = _context(Decimal("100"), date(2027, 1, 1))
        leg = _leg(3, Decimal("100"), date(2027, 1, 1))

        totals = aggregate_greeks((leg,), context, _greeks())

        assert totals["delta"] == Decimal("0.5") * 3
        assert totals["gamma"] == Decimal("0.02") * 3
        assert totals["vega"] == Decimal("10") * 3

    def test_short_matching_leg_negates_totals(self) -> None:
        context = _context(Decimal("100"), date(2027, 1, 1))
        leg = _leg(-2, Decimal("100"), date(2027, 1, 1))

        totals = aggregate_greeks((leg,), context, _greeks())

        assert totals["delta"] == Decimal("0.5") * -2

    def test_multiplier_scales_totals(self) -> None:
        context = _context(Decimal("100"), date(2027, 1, 1))
        leg = StrategyLeg(
            strike=Decimal("100"), option_type=OptionType.CALL, quantity=1, premium=Decimal("5"),
            expiry=date(2027, 1, 1), multiplier=75,
        )

        totals = aggregate_greeks((leg,), context, _greeks())

        assert totals["delta"] == Decimal("0.5") * 75


class TestNonMatchingLegUsesGammaAdjustedApproximation:
    def test_call_leg_above_reference_strike_uses_positive_shift(self) -> None:
        """strike_shift = 110-100=10, sign=+1 for CALL ->
        approx_delta = (0.5 + 0.02*10*1) = 0.7, scaled by quantity 1."""
        context = _context(Decimal("100"), date(2027, 1, 1))
        leg = _leg(1, Decimal("110"), date(2027, 1, 1), OptionType.CALL)

        totals = aggregate_greeks((leg,), context, _greeks())

        assert totals["delta"] == Decimal("0.5") + Decimal("0.02") * Decimal("10")
        assert totals["gamma"] == Decimal("0.02")  # gamma itself is not approximated

    def test_put_leg_flips_the_sign_of_the_shift(self) -> None:
        """PUT sign=-1 -> approx_delta = 0.5 + 0.02*10*(-1) = 0.3."""
        context = _context(Decimal("100"), date(2027, 1, 1))
        leg = _leg(1, Decimal("110"), date(2027, 1, 1), OptionType.PUT)

        totals = aggregate_greeks((leg,), context, _greeks())

        assert totals["delta"] == Decimal("0.5") - Decimal("0.02") * Decimal("10")

    def test_different_expiry_alone_triggers_approximation_path(self) -> None:
        """Same strike as reference, but a different expiry -- shift is 0,
        so delta is unchanged, but this still exercises the "else" branch
        rather than the exact-match branch."""
        context = _context(Decimal("100"), date(2027, 1, 1))
        leg = _leg(1, Decimal("100"), date(2027, 6, 1))

        totals = aggregate_greeks((leg,), context, _greeks())

        assert totals["delta"] == Decimal("0.5")  # shift=0, so numerically identical either path


class TestMultiLegPortfolio:
    def test_totals_are_additive_across_legs(self) -> None:
        context = _context(Decimal("100"), date(2027, 1, 1))
        legs = (
            _leg(1, Decimal("100"), date(2027, 1, 1)),
            _leg(-1, Decimal("100"), date(2027, 1, 1)),
        )

        totals = aggregate_greeks(legs, context, _greeks())

        assert totals["delta"] == Decimal("0")  # long + short cancel exactly

    def test_empty_legs_returns_all_zero_totals(self) -> None:
        context = _context(Decimal("100"), date(2027, 1, 1))

        totals = aggregate_greeks((), context, _greeks())

        assert all(value == Decimal("0") for value in totals.values())
