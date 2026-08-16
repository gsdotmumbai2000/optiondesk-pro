"""Tests for expiry payoff arithmetic: leg_expiry_pnl, total_expiry_pnl,
leg_intrinsic_exposure. Pure arithmetic -- every expected value here is
hand-computed, not re-derived from the code under test.
"""

from datetime import date
from decimal import Decimal

from app.payoff.analytics.expiry_payoff import (
    leg_expiry_pnl,
    leg_intrinsic_exposure,
    total_expiry_pnl,
)
from app.payoff.models.legs import StrategyLeg
from app.pricing.models.enums import OptionType


def _leg(
    option_type: OptionType, quantity: int, strike: Decimal, premium: Decimal, *, multiplier: int = 1,
) -> StrategyLeg:
    return StrategyLeg(
        strike=strike, option_type=option_type, quantity=quantity, premium=premium,
        expiry=date(2027, 1, 1), multiplier=multiplier,
    )


class TestLegExpiryPnl:
    def test_long_call_itm_at_expiry(self) -> None:
        """Buy 1 call, strike 100, premium 5; spot 110 -> intrinsic 10,
        pnl = 1*10 - 1*5 = 5."""
        leg = _leg(OptionType.CALL, 1, Decimal("100"), Decimal("5"))

        assert leg_expiry_pnl(Decimal("110"), leg) == Decimal("5")

    def test_long_call_otm_at_expiry_loses_full_premium(self) -> None:
        """Buy 1 call, strike 100, premium 5; spot 90 -> intrinsic 0,
        pnl = -5 (full premium loss)."""
        leg = _leg(OptionType.CALL, 1, Decimal("100"), Decimal("5"))

        assert leg_expiry_pnl(Decimal("90"), leg) == Decimal("-5")

    def test_short_put_itm_at_expiry(self) -> None:
        """Sell 1 put (quantity=-1), strike 100, premium 5; spot 90 ->
        intrinsic 10, pnl = -1*10 - (-1)*5 = -10 + 5 = -5."""
        leg = _leg(OptionType.PUT, -1, Decimal("100"), Decimal("5"))

        assert leg_expiry_pnl(Decimal("90"), leg) == Decimal("-5")

    def test_short_put_otm_at_expiry_keeps_full_premium(self) -> None:
        """Sell 1 put, strike 100, premium 5; spot 110 -> intrinsic 0,
        pnl = 0 - (-1)*5 = 5."""
        leg = _leg(OptionType.PUT, -1, Decimal("100"), Decimal("5"))

        assert leg_expiry_pnl(Decimal("110"), leg) == Decimal("5")

    def test_multiplier_scales_pnl(self) -> None:
        leg = _leg(OptionType.CALL, 1, Decimal("100"), Decimal("5"), multiplier=75)

        assert leg_expiry_pnl(Decimal("110"), leg) == Decimal("5") * 75


class TestTotalExpiryPnl:
    def test_bull_call_spread_max_gain_above_both_strikes(self) -> None:
        """Buy 100C @5, sell 110C @2 (net debit 3). At spot 120 (above both
        strikes): long leg = 20-5=15, short leg = -1*10 - (-1)*2 = -8.
        Total = 15 - 8 = 7 = (110-100) - (5-2) = 10-3."""
        legs = (
            _leg(OptionType.CALL, 1, Decimal("100"), Decimal("5")),
            _leg(OptionType.CALL, -1, Decimal("110"), Decimal("2")),
        )

        assert total_expiry_pnl(Decimal("120"), legs) == Decimal("7")

    def test_bull_call_spread_max_loss_below_both_strikes(self) -> None:
        """At spot 90 (below both strikes): both expire worthless, net loss
        = -(5-2) = -3 (the net debit paid)."""
        legs = (
            _leg(OptionType.CALL, 1, Decimal("100"), Decimal("5")),
            _leg(OptionType.CALL, -1, Decimal("110"), Decimal("2")),
        )

        assert total_expiry_pnl(Decimal("90"), legs) == Decimal("-3")

    def test_empty_legs_returns_zero(self) -> None:
        assert total_expiry_pnl(Decimal("100"), ()) == Decimal("0")


class TestLegIntrinsicExposure:
    def test_long_call_is_positive(self) -> None:
        leg = _leg(OptionType.CALL, 3, Decimal("100"), Decimal("5"))

        assert leg_intrinsic_exposure(leg) == Decimal("3")

    def test_short_call_is_negative(self) -> None:
        leg = _leg(OptionType.CALL, -3, Decimal("100"), Decimal("5"))

        assert leg_intrinsic_exposure(leg) == Decimal("-3")

    def test_long_put_is_negative(self) -> None:
        leg = _leg(OptionType.PUT, 3, Decimal("100"), Decimal("5"))

        assert leg_intrinsic_exposure(leg) == Decimal("-3")

    def test_short_put_is_positive(self) -> None:
        leg = _leg(OptionType.PUT, -3, Decimal("100"), Decimal("5"))

        assert leg_intrinsic_exposure(leg) == Decimal("3")
