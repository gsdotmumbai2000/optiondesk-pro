"""Tests for build_payoff_curve(): price-range bounds and point sampling."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.payoff.analytics.expiry_payoff import total_expiry_pnl
from app.payoff.analytics.payoff_curve import DEFAULT_SAMPLES, build_payoff_curve
from app.payoff.models.legs import StrategyLeg
from app.pricing.models.enums import OptionType


def _context(spot: Decimal, tick_size: Decimal = Decimal("0.05")) -> SimpleNamespace:
    return SimpleNamespace(spot_price=spot, tick_size=tick_size)


def _leg(option_type: OptionType, strike: Decimal) -> StrategyLeg:
    return StrategyLeg(
        strike=strike, option_type=option_type, quantity=1, premium=Decimal("5"), expiry=date(2027, 1, 1),
    )


class TestPriceBounds:
    def test_bounds_derive_from_strikes_and_spot(self) -> None:
        """Legs at 90 and 110, spot 100 -> low = min(90,100)*0.7 = 63,
        high = max(110,100)*1.3 = 143."""
        legs = (_leg(OptionType.PUT, Decimal("90")), _leg(OptionType.CALL, Decimal("110")))
        curve = build_payoff_curve(legs, _context(Decimal("100")))

        assert curve.points[0].underlying_price == Decimal("63")
        assert curve.points[-1].underlying_price == Decimal("143")

    def test_bounds_fall_back_to_spot_only_when_no_positive_strike_legs(self) -> None:
        """A leg with strike=0 (e.g. a synthetic/stock leg) doesn't count as
        a "strike" for bounds purposes -- falls back to spot*0.7/spot*1.3."""
        legs = (_leg(OptionType.CALL, Decimal("0")),)
        curve = build_payoff_curve(legs, _context(Decimal("100")))

        assert curve.points[0].underlying_price == Decimal("70.0")
        assert curve.points[-1].underlying_price == Decimal("130.0")


class TestPointSampling:
    def test_default_sample_count_matches_default_samples(self) -> None:
        """Strike (100) coincides exactly with a grid point here (evenly
        spaced 70..130), so no extra point is injected -- count matches
        DEFAULT_SAMPLES exactly. See TestStrikeInjection for the case
        where it doesn't coincide."""
        legs = (_leg(OptionType.CALL, Decimal("100")),)
        curve = build_payoff_curve(legs, _context(Decimal("100")))

        assert len(curve.points) == DEFAULT_SAMPLES

    def test_custom_sample_count_is_honored(self) -> None:
        legs = (_leg(OptionType.CALL, Decimal("100")),)
        curve = build_payoff_curve(legs, _context(Decimal("100")), samples=5)

        assert len(curve.points) == 5

    def test_points_are_evenly_spaced(self) -> None:
        legs = (_leg(OptionType.CALL, Decimal("100")),)
        curve = build_payoff_curve(legs, _context(Decimal("100")), samples=5)

        gaps = [
            curve.points[i + 1].underlying_price - curve.points[i].underlying_price
            for i in range(len(curve.points) - 1)
        ]
        assert all(gap == gaps[0] for gap in gaps)

    def test_each_point_pnl_matches_total_expiry_pnl_at_that_price(self) -> None:
        """The curve is just total_expiry_pnl() sampled across the price
        range -- cross-checked directly against that function."""
        legs = (_leg(OptionType.CALL, Decimal("100")), _leg(OptionType.PUT, Decimal("90")))
        curve = build_payoff_curve(legs, _context(Decimal("100")), samples=7)

        for point in curve.points:
            assert point.pnl == total_expiry_pnl(point.underlying_price, legs)


class TestStrikeInjection:
    """Regression coverage for the chart-overshoot bug: a wide auto-scaled
    price range with a sparse grid can land zero sample points inside a
    narrow strike gap, which visibly distorts a spline-rendered curve near
    that strike -- each leg's exact strike must always be a sample point."""

    def test_strike_not_on_grid_is_injected_as_extra_point(self) -> None:
        """Bull call spread (100/110) at spot 105: low=70, high=143, and
        neither strike lands exactly on the evenly-spaced 21-point grid."""
        legs = (_leg(OptionType.CALL, Decimal("100")), _leg(OptionType.CALL, Decimal("110")))
        curve = build_payoff_curve(legs, _context(Decimal("105")), samples=21)

        prices = {point.underlying_price for point in curve.points}
        assert Decimal("100") in prices
        assert Decimal("110") in prices
        assert len(curve.points) > 21  # both strikes added as extras

    def test_strike_already_on_grid_adds_no_duplicate(self) -> None:
        legs = (_leg(OptionType.CALL, Decimal("100")),)
        curve = build_payoff_curve(legs, _context(Decimal("100")), samples=21)

        assert len(curve.points) == 21

    def test_out_of_range_strike_is_not_injected(self) -> None:
        """A leg with strike=0 (synthetic) falls outside [low, high] and
        must not be injected as a sample point."""
        legs = (_leg(OptionType.CALL, Decimal("0")),)
        curve = build_payoff_curve(legs, _context(Decimal("100")), samples=21)

        assert len(curve.points) == 21


class TestEmptyOrDegenerateInputs:
    def test_empty_legs_returns_empty_curve(self) -> None:
        curve = build_payoff_curve((), _context(Decimal("100")))

        assert curve.points == ()

    def test_samples_below_two_returns_empty_curve(self) -> None:
        legs = (_leg(OptionType.CALL, Decimal("100")),)

        assert build_payoff_curve(legs, _context(Decimal("100")), samples=1).points == ()
        assert build_payoff_curve(legs, _context(Decimal("100")), samples=0).points == ()
