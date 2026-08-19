"""Tests for build_leg_from_inputs(): the Add Leg dialog's pure form-to-
StrategyLeg parsing/validation, deliberately extracted so it's testable
without a Qt event loop.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.strategy.models.enums import LegKind
from app.ui.dialogs.add_leg_dialog import build_leg_from_inputs

_EXPIRY = date(2026, 8, 18)


def _build(**overrides):
    defaults = dict(
        underlying="NIFTY", exchange="NFO", expiry=_EXPIRY,
        right="CE", side="Buy", lots=1,
        strike_text="24500", premium_text="120.5", lot_size=75,
    )
    defaults.update(overrides)
    return build_leg_from_inputs(**defaults)


class TestRightSideMapping:
    @pytest.mark.parametrize(
        "right,side,expected",
        [
            ("CE", "Buy", LegKind.CALL_BUY),
            ("CE", "Sell", LegKind.CALL_SELL),
            ("PE", "Buy", LegKind.PUT_BUY),
            ("PE", "Sell", LegKind.PUT_SELL),
        ],
    )
    def test_maps_right_and_side_to_leg_kind(self, right, side, expected) -> None:
        leg = _build(right=right, side=side)

        assert leg.kind == expected

    def test_unsupported_combination_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported right/side"):
            _build(right="FUT", side="Buy")


class TestFieldPopulation:
    def test_populates_all_fields_from_inputs(self) -> None:
        leg = _build()

        assert leg.underlying == "NIFTY"
        assert leg.exchange == "NFO"
        assert leg.expiry == _EXPIRY
        assert leg.quantity == 1
        assert leg.strike == Decimal("24500")
        assert leg.premium == Decimal("120.5")
        assert leg.multiplier == 75
        assert leg.leg_id  # generated, non-empty

    def test_each_call_generates_a_distinct_leg_id(self) -> None:
        leg_a = _build()
        leg_b = _build()

        assert leg_a.leg_id != leg_b.leg_id


class TestValidation:
    def test_zero_lots_raises(self) -> None:
        with pytest.raises(ValueError, match="Quantity"):
            _build(lots=0)

    def test_negative_lots_raises(self) -> None:
        with pytest.raises(ValueError, match="Quantity"):
            _build(lots=-1)

    def test_non_numeric_strike_raises(self) -> None:
        with pytest.raises(ValueError, match="Strike must be a number"):
            _build(strike_text="not-a-number")

    def test_zero_strike_raises(self) -> None:
        with pytest.raises(ValueError, match="Strike must be positive"):
            _build(strike_text="0")

    def test_negative_strike_raises(self) -> None:
        with pytest.raises(ValueError, match="Strike must be positive"):
            _build(strike_text="-100")

    def test_non_numeric_premium_raises(self) -> None:
        with pytest.raises(ValueError, match="Premium must be a number"):
            _build(premium_text="abc")

    def test_zero_premium_raises(self) -> None:
        with pytest.raises(ValueError, match="Premium must be positive"):
            _build(premium_text="0")
