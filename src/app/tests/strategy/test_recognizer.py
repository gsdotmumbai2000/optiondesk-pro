"""Tests for recognize_strategy(): pure leg-composition pattern matching,
no external dependencies -- covers both the pre-existing patterns and the
gaps the roadmap flagged (ratios, diagonals, broken-wing butterflies,
collars), plus a real bug this work found: CALENDAR_SPREAD was unreachable
because CALL_BUY+CALL_SELL/PUT_BUY+PUT_SELL always matched the
vertical-spread branch before the calendar fallback could ever run.
"""

from datetime import date
from decimal import Decimal

from app.strategy.models.enums import LegKind, StrategyType
from app.strategy.models.leg import StrategyLeg
from app.strategy.recognition.recognizer import recognize_strategy

_E1 = date(2026, 8, 18)
_E2 = date(2026, 9, 24)


def _leg(kind: LegKind, strike: str, *, quantity: int = 1, expiry: date = _E1) -> StrategyLeg:
    return StrategyLeg(
        leg_id="L", kind=kind, quantity=quantity, premium=Decimal("0"),
        strike=Decimal(strike), expiry=expiry,
    )


class TestEmptyAndSingleLeg:
    def test_no_legs_is_custom(self) -> None:
        assert recognize_strategy(()) == StrategyType.CUSTOM

    def test_single_call_buy_is_long_call(self) -> None:
        assert recognize_strategy((_leg(LegKind.CALL_BUY, "24500"),)) == StrategyType.LONG_CALL

    def test_single_put_sell_is_short_put(self) -> None:
        assert recognize_strategy((_leg(LegKind.PUT_SELL, "24000"),)) == StrategyType.SHORT_PUT


class TestStraddlesAndStrangles:
    def test_same_strike_calls_and_puts_buy_is_long_straddle(self) -> None:
        legs = (_leg(LegKind.CALL_BUY, "24500"), _leg(LegKind.PUT_BUY, "24500"))
        assert recognize_strategy(legs) == StrategyType.LONG_STRADDLE

    def test_different_strike_calls_and_puts_buy_is_long_strangle(self) -> None:
        legs = (_leg(LegKind.CALL_BUY, "24600"), _leg(LegKind.PUT_BUY, "24400"))
        assert recognize_strategy(legs) == StrategyType.LONG_STRANGLE

    def test_same_strike_calls_and_puts_sell_is_short_straddle(self) -> None:
        legs = (_leg(LegKind.CALL_SELL, "24500"), _leg(LegKind.PUT_SELL, "24500"))
        assert recognize_strategy(legs) == StrategyType.SHORT_STRADDLE


class TestVerticalSpreadsUnchanged:
    def test_lower_strike_call_buy_higher_call_sell_same_expiry_is_bull_call_spread(self) -> None:
        legs = (_leg(LegKind.CALL_BUY, "24400"), _leg(LegKind.CALL_SELL, "24600"))
        assert recognize_strategy(legs) == StrategyType.BULL_CALL_SPREAD

    def test_higher_strike_call_buy_lower_call_sell_same_expiry_is_bear_call_spread(self) -> None:
        legs = (_leg(LegKind.CALL_BUY, "24600"), _leg(LegKind.CALL_SELL, "24400"))
        assert recognize_strategy(legs) == StrategyType.BEAR_CALL_SPREAD

    def test_put_spread_same_expiry_is_bull_or_bear_put_spread(self) -> None:
        legs = (_leg(LegKind.PUT_BUY, "24600"), _leg(LegKind.PUT_SELL, "24400"))
        assert recognize_strategy(legs) == StrategyType.BEAR_PUT_SPREAD


class TestCalendarAndDiagonalSpreads:
    """The real bug: same strike + different expiry previously fell through
    to a vertical-spread verdict (or worse, a wrong one when strikes were
    equal) because _calendar() was unreachable dead code."""

    def test_same_strike_different_expiry_call_is_calendar_spread(self) -> None:
        legs = (_leg(LegKind.CALL_BUY, "24500", expiry=_E1), _leg(LegKind.CALL_SELL, "24500", expiry=_E2))
        assert recognize_strategy(legs) == StrategyType.CALENDAR_SPREAD

    def test_same_strike_different_expiry_put_is_calendar_spread(self) -> None:
        legs = (_leg(LegKind.PUT_BUY, "24500", expiry=_E1), _leg(LegKind.PUT_SELL, "24500", expiry=_E2))
        assert recognize_strategy(legs) == StrategyType.CALENDAR_SPREAD

    def test_different_strike_and_different_expiry_call_is_diagonal_spread(self) -> None:
        legs = (_leg(LegKind.CALL_BUY, "24400", expiry=_E1), _leg(LegKind.CALL_SELL, "24600", expiry=_E2))
        assert recognize_strategy(legs) == StrategyType.DIAGONAL_SPREAD

    def test_different_strike_and_different_expiry_put_is_diagonal_spread(self) -> None:
        legs = (_leg(LegKind.PUT_BUY, "24400", expiry=_E1), _leg(LegKind.PUT_SELL, "24600", expiry=_E2))
        assert recognize_strategy(legs) == StrategyType.DIAGONAL_SPREAD

    def test_same_expiry_is_never_misclassified_as_calendar_or_diagonal(self) -> None:
        legs = (_leg(LegKind.CALL_BUY, "24500", expiry=_E1), _leg(LegKind.CALL_SELL, "24500", expiry=_E1))
        result = recognize_strategy(legs)
        assert result not in (StrategyType.CALENDAR_SPREAD, StrategyType.DIAGONAL_SPREAD)


class TestRatioSpread:
    def test_unequal_quantity_same_right_same_expiry_is_ratio_spread(self) -> None:
        legs = (
            _leg(LegKind.CALL_BUY, "24400", quantity=1),
            _leg(LegKind.CALL_SELL, "24600", quantity=2),
        )
        assert recognize_strategy(legs) == StrategyType.RATIO_SPREAD

    def test_equal_quantity_same_right_same_expiry_is_not_ratio_spread(self) -> None:
        legs = (
            _leg(LegKind.CALL_BUY, "24400", quantity=2),
            _leg(LegKind.CALL_SELL, "24600", quantity=2),
        )
        assert recognize_strategy(legs) == StrategyType.BULL_CALL_SPREAD


class TestSyntheticAndStockCombinations:
    def test_call_buy_put_sell_same_strike_is_synthetic_future(self) -> None:
        legs = (_leg(LegKind.CALL_BUY, "24500"), _leg(LegKind.PUT_SELL, "24500"))
        assert recognize_strategy(legs) == StrategyType.SYNTHETIC_FUTURE

    def test_stock_buy_and_call_sell_is_covered_call(self) -> None:
        legs = (_leg(LegKind.STOCK_BUY, "0"), _leg(LegKind.CALL_SELL, "24500"))
        assert recognize_strategy(legs) == StrategyType.COVERED_CALL

    def test_stock_buy_and_put_buy_is_protective_put(self) -> None:
        legs = (_leg(LegKind.STOCK_BUY, "0"), _leg(LegKind.PUT_BUY, "24000"))
        assert recognize_strategy(legs) == StrategyType.PROTECTIVE_PUT


class TestCollar:
    def test_stock_put_buy_call_sell_is_collar(self) -> None:
        legs = (
            _leg(LegKind.STOCK_BUY, "0"),
            _leg(LegKind.PUT_BUY, "24000"),
            _leg(LegKind.CALL_SELL, "25000"),
        )
        assert recognize_strategy(legs) == StrategyType.COLLAR


class TestJadeLizardTightened:
    def test_full_triple_is_jade_lizard(self) -> None:
        legs = (
            _leg(LegKind.PUT_SELL, "24000"),
            _leg(LegKind.CALL_SELL, "25000"),
            _leg(LegKind.CALL_BUY, "25200"),
        )
        assert recognize_strategy(legs) == StrategyType.JADE_LIZARD

    def test_call_buy_and_put_sell_without_call_sell_is_not_jade_lizard(self) -> None:
        """Previously matched on CALL_BUY==1 and PUT_SELL==1 alone, with no
        check on the third leg -- a real gap this closes."""
        legs = (
            _leg(LegKind.CALL_BUY, "24500"),
            _leg(LegKind.PUT_SELL, "24000"),
            _leg(LegKind.STOCK_BUY, "0"),
        )
        assert recognize_strategy(legs) != StrategyType.JADE_LIZARD


class TestButterflyAndBrokenWing:
    def test_symmetric_wings_is_butterfly(self) -> None:
        legs = (
            _leg(LegKind.CALL_BUY, "24400", quantity=1),
            _leg(LegKind.CALL_SELL, "24500", quantity=2),
            _leg(LegKind.CALL_BUY, "24600", quantity=1),
        )
        assert recognize_strategy(legs) == StrategyType.BUTTERFLY

    def test_asymmetric_wings_is_broken_wing_butterfly(self) -> None:
        legs = (
            _leg(LegKind.CALL_BUY, "24300", quantity=1),  # 200-wide lower wing
            _leg(LegKind.CALL_SELL, "24500", quantity=2),
            _leg(LegKind.CALL_BUY, "24600", quantity=1),  # 100-wide upper wing
        )
        assert recognize_strategy(legs) == StrategyType.BROKEN_WING_BUTTERFLY

    def test_put_butterfly_recognized_too(self) -> None:
        legs = (
            _leg(LegKind.PUT_BUY, "24400", quantity=1),
            _leg(LegKind.PUT_SELL, "24500", quantity=2),
            _leg(LegKind.PUT_BUY, "24600", quantity=1),
        )
        assert recognize_strategy(legs) == StrategyType.BUTTERFLY

    def test_mismatched_middle_quantity_is_not_a_butterfly(self) -> None:
        """Middle leg must offset both wings (1:2:1 or generalized
        low_qty+high_qty); an arbitrary quantity is not a real butterfly."""
        legs = (
            _leg(LegKind.CALL_BUY, "24400", quantity=1),
            _leg(LegKind.CALL_SELL, "24500", quantity=1),  # should be 2
            _leg(LegKind.CALL_BUY, "24600", quantity=1),
        )
        assert recognize_strategy(legs) not in (StrategyType.BUTTERFLY, StrategyType.BROKEN_WING_BUTTERFLY)

    def test_mixed_call_and_put_legs_is_not_a_butterfly(self) -> None:
        legs = (
            _leg(LegKind.CALL_BUY, "24400", quantity=1),
            _leg(LegKind.PUT_SELL, "24500", quantity=2),
            _leg(LegKind.CALL_BUY, "24600", quantity=1),
        )
        assert recognize_strategy(legs) not in (StrategyType.BUTTERFLY, StrategyType.BROKEN_WING_BUTTERFLY)

    def test_three_unrelated_legs_fall_back_to_custom(self) -> None:
        legs = (
            _leg(LegKind.CALL_BUY, "24400"),
            _leg(LegKind.CALL_BUY, "24500"),
            _leg(LegKind.PUT_BUY, "24000"),
        )
        assert recognize_strategy(legs) == StrategyType.CUSTOM


class TestFourLegStructuresUnchanged:
    def test_wide_iron_condor(self) -> None:
        legs = (
            _leg(LegKind.PUT_BUY, "24000"), _leg(LegKind.PUT_SELL, "24200"),
            _leg(LegKind.CALL_SELL, "24800"), _leg(LegKind.CALL_BUY, "25000"),
        )
        assert recognize_strategy(legs) == StrategyType.IRON_CONDOR

    def test_same_strike_wings_is_iron_butterfly(self) -> None:
        legs = (
            _leg(LegKind.PUT_BUY, "24000"), _leg(LegKind.PUT_SELL, "24500"),
            _leg(LegKind.CALL_SELL, "24500"), _leg(LegKind.CALL_BUY, "25000"),
        )
        assert recognize_strategy(legs) == StrategyType.IRON_BUTTERFLY

    def test_sold_strikes_differ_and_not_iron_condor_shape_is_box_spread(self) -> None:
        """A box spread's sold legs (call and put) sit at different
        strikes, so it must fall through past both iron_condor and
        iron_butterfly to the BOX_SPREAD fallback."""
        legs = (
            _leg(LegKind.CALL_BUY, "24000"), _leg(LegKind.CALL_SELL, "24500"),
            _leg(LegKind.PUT_BUY, "24500"), _leg(LegKind.PUT_SELL, "24000"),
        )
        assert recognize_strategy(legs) == StrategyType.BOX_SPREAD


class TestFiveLegsFallsBackToCustom:
    def test_five_legs_is_custom(self) -> None:
        legs = tuple(_leg(LegKind.CALL_BUY, str(24000 + i * 100)) for i in range(5))
        assert recognize_strategy(legs) == StrategyType.CUSTOM
