"""Strategy recognition patterns (display/reporting only)."""

from collections import Counter

from app.strategy.models.enums import LegKind, StrategyType
from app.strategy.models.leg import StrategyLeg


def recognize_strategy(legs: tuple[StrategyLeg, ...]) -> StrategyType:
    """Identify strategy type from leg composition."""
    if not legs:
        return StrategyType.CUSTOM
    if len(legs) == 1:
        return _single_leg(legs[0])
    if len(legs) == 2:
        return _two_legs(legs)
    if len(legs) == 3:
        return _three_legs(legs)
    if len(legs) == 4:
        return _four_legs(legs)
    return StrategyType.CUSTOM


def _single_leg(leg: StrategyLeg) -> StrategyType:
    mapping = {
        LegKind.CALL_BUY: StrategyType.LONG_CALL,
        LegKind.CALL_SELL: StrategyType.SHORT_CALL,
        LegKind.PUT_BUY: StrategyType.LONG_PUT,
        LegKind.PUT_SELL: StrategyType.SHORT_PUT,
    }
    return mapping.get(leg.kind, StrategyType.CUSTOM)


def _two_legs(legs: tuple[StrategyLeg, ...]) -> StrategyType:
    kinds = {leg.kind for leg in legs}
    if kinds == {LegKind.CALL_BUY, LegKind.PUT_BUY}:
        if _same_strike(legs):
            return StrategyType.LONG_STRADDLE
        return StrategyType.LONG_STRANGLE
    if kinds == {LegKind.CALL_SELL, LegKind.PUT_SELL}:
        if _same_strike(legs):
            return StrategyType.SHORT_STRADDLE
        return StrategyType.SHORT_STRANGLE
    if kinds == {LegKind.CALL_BUY, LegKind.CALL_SELL}:
        return _vertical_spread(legs, is_call=True)
    if kinds == {LegKind.PUT_BUY, LegKind.PUT_SELL}:
        return _vertical_spread(legs, is_call=False)
    if kinds == {LegKind.CALL_BUY, LegKind.PUT_SELL}:
        return StrategyType.SYNTHETIC_FUTURE
    if kinds == {LegKind.STOCK_BUY, LegKind.CALL_SELL}:
        return StrategyType.COVERED_CALL
    if kinds == {LegKind.STOCK_BUY, LegKind.PUT_BUY}:
        return StrategyType.PROTECTIVE_PUT
    if _calendar(legs):
        return StrategyType.CALENDAR_SPREAD
    return StrategyType.CUSTOM


def _three_legs(legs: tuple[StrategyLeg, ...]) -> StrategyType:
    kinds = Counter(leg.kind for leg in legs)
    if kinds.get(LegKind.CALL_BUY, 0) == 1 and kinds.get(LegKind.PUT_SELL, 0) == 1:
        return StrategyType.JADE_LIZARD
    if sum(kinds.values()) == 3 and LegKind.CALL_BUY in kinds:
        return StrategyType.BUTTERFLY
    return StrategyType.CUSTOM


def _four_legs(legs: tuple[StrategyLeg, ...]) -> StrategyType:
    kinds = Counter(leg.kind for leg in legs)
    if kinds == Counter(
        {LegKind.PUT_BUY: 1, LegKind.PUT_SELL: 1, LegKind.CALL_BUY: 1, LegKind.CALL_SELL: 1}
    ):
        if _iron_condor(legs):
            return StrategyType.IRON_CONDOR
        if _same_strike(legs):
            return StrategyType.IRON_BUTTERFLY
        return StrategyType.BOX_SPREAD
    return StrategyType.CUSTOM


def _same_strike(legs: tuple[StrategyLeg, ...]) -> bool:
    strikes = {leg.strike for leg in legs if leg.strike > 0}
    return len(strikes) == 1


def _vertical_spread(legs: tuple[StrategyLeg, ...], *, is_call: bool) -> StrategyType:
    buy = next((l for l in legs if l.kind.name.endswith("BUY")), None)
    sell = next((l for l in legs if l.kind.name.endswith("SELL")), None)
    if buy is None or sell is None:
        return StrategyType.CUSTOM
    if buy.strike < sell.strike:
        return StrategyType.BULL_CALL_SPREAD if is_call else StrategyType.BULL_PUT_SPREAD
    return StrategyType.BEAR_CALL_SPREAD if is_call else StrategyType.BEAR_PUT_SPREAD


def _calendar(legs: tuple[StrategyLeg, ...]) -> bool:
    expiries = {leg.expiry for leg in legs if leg.expiry}
    return len(expiries) == 2 and _same_strike(legs)


def _iron_condor(legs: tuple[StrategyLeg, ...]) -> bool:
    puts = sorted(l.strike for l in legs if "PUT" in l.kind.value)
    calls = sorted(l.strike for l in legs if "CALL" in l.kind.value)
    return len(puts) == 2 and len(calls) == 2 and puts[0] < puts[1] < calls[0] < calls[1]
