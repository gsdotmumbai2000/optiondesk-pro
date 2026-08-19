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
        return _same_right_spread(legs, is_call=True)
    if kinds == {LegKind.PUT_BUY, LegKind.PUT_SELL}:
        return _same_right_spread(legs, is_call=False)
    if kinds == {LegKind.CALL_BUY, LegKind.PUT_SELL}:
        return StrategyType.SYNTHETIC_FUTURE
    if kinds == {LegKind.STOCK_BUY, LegKind.CALL_SELL}:
        return StrategyType.COVERED_CALL
    if kinds == {LegKind.STOCK_BUY, LegKind.PUT_BUY}:
        return StrategyType.PROTECTIVE_PUT
    return StrategyType.CUSTOM


def _same_right_spread(legs: tuple[StrategyLeg, ...], *, is_call: bool) -> StrategyType:
    """Classify a two-leg, same-right (both calls or both puts) BUY+SELL
    combination: calendar (same strike, different expiry), diagonal
    (different strike *and* expiry), ratio (same strike/expiry, unequal
    quantities), or a plain vertical spread.

    Previously every same-right BUY+SELL pair went straight to a vertical-
    spread verdict regardless of expiry, so a real calendar spread (same
    strike, different expiry) fell into whichever vertical-spread branch
    strike comparison produced -- silently wrong, and the separate
    `_calendar()` fallback that was meant to catch this could never actually
    run, since CALL_BUY+CALL_SELL/PUT_BUY+PUT_SELL always matched the
    vertical-spread check first.
    """
    buy = next(l for l in legs if l.kind.name.endswith("BUY"))
    sell = next(l for l in legs if l.kind.name.endswith("SELL"))
    if buy.expiry != sell.expiry:
        return StrategyType.CALENDAR_SPREAD if buy.strike == sell.strike else StrategyType.DIAGONAL_SPREAD
    if buy.quantity != sell.quantity:
        return StrategyType.RATIO_SPREAD
    if buy.strike < sell.strike:
        return StrategyType.BULL_CALL_SPREAD if is_call else StrategyType.BULL_PUT_SPREAD
    return StrategyType.BEAR_CALL_SPREAD if is_call else StrategyType.BEAR_PUT_SPREAD


def _three_legs(legs: tuple[StrategyLeg, ...]) -> StrategyType:
    kinds = Counter(leg.kind for leg in legs)
    if kinds == Counter({LegKind.PUT_SELL: 1, LegKind.CALL_SELL: 1, LegKind.CALL_BUY: 1}):
        return StrategyType.JADE_LIZARD
    if kinds == Counter({LegKind.STOCK_BUY: 1, LegKind.PUT_BUY: 1, LegKind.CALL_SELL: 1}):
        return StrategyType.COLLAR
    butterfly = _classify_butterfly(legs)
    if butterfly is not None:
        return butterfly
    return StrategyType.CUSTOM


def _four_legs(legs: tuple[StrategyLeg, ...]) -> StrategyType:
    kinds = Counter(leg.kind for leg in legs)
    if kinds == Counter(
        {LegKind.PUT_BUY: 1, LegKind.PUT_SELL: 1, LegKind.CALL_BUY: 1, LegKind.CALL_SELL: 1}
    ):
        if _iron_condor(legs):
            return StrategyType.IRON_CONDOR
        if _iron_butterfly(legs):
            return StrategyType.IRON_BUTTERFLY
        return StrategyType.BOX_SPREAD
    return StrategyType.CUSTOM


def _same_strike(legs: tuple[StrategyLeg, ...]) -> bool:
    strikes = {leg.strike for leg in legs if leg.strike > 0}
    return len(strikes) == 1


def _classify_butterfly(legs: tuple[StrategyLeg, ...]) -> StrategyType | None:
    """A butterfly is two long wings and a doubled short body, all the same
    option right: buy low, sell mid (quantity = low_qty + high_qty), buy
    high. Equal wing widths (mid-low == high-mid) makes it a symmetric
    BUTTERFLY; unequal widths make it a BROKEN_WING_BUTTERFLY. Returns None
    for anything that isn't this shape (previous check only tested "3 legs
    with a CALL_BUY present", which matched unrelated 3-leg combinations
    too loosely and never distinguished the broken-wing variant)."""
    rights = {_option_right(leg) for leg in legs}
    if len(rights) != 1 or None in rights:
        return None
    buys = sorted((l for l in legs if l.kind.name.endswith("BUY")), key=lambda l: l.strike)
    sells = [l for l in legs if l.kind.name.endswith("SELL")]
    if len(buys) != 2 or len(sells) != 1:
        return None
    low, high = buys
    mid = sells[0]
    if not (low.strike < mid.strike < high.strike):
        return None
    if mid.quantity != low.quantity + high.quantity:
        return None
    lower_wing = mid.strike - low.strike
    upper_wing = high.strike - mid.strike
    return StrategyType.BUTTERFLY if lower_wing == upper_wing else StrategyType.BROKEN_WING_BUTTERFLY


def _option_right(leg: StrategyLeg) -> str | None:
    if "CALL" in leg.kind.value:
        return "CALL"
    if "PUT" in leg.kind.value:
        return "PUT"
    return None


def _iron_condor(legs: tuple[StrategyLeg, ...]) -> bool:
    puts = sorted(l.strike for l in legs if "PUT" in l.kind.value)
    calls = sorted(l.strike for l in legs if "CALL" in l.kind.value)
    return len(puts) == 2 and len(calls) == 2 and puts[0] < puts[1] < calls[0] < calls[1]


def _iron_butterfly(legs: tuple[StrategyLeg, ...]) -> bool:
    """An iron butterfly is a short straddle (the sold put and sold call
    share one strike) protected by wings at different strikes -- the wings
    necessarily differ from the body, so this must only compare the two
    *sold* legs' strikes, not all four (which no real iron butterfly could
    ever satisfy)."""
    sold_strikes = {l.strike for l in legs if l.kind.name.endswith("SELL")}
    return len(sold_strikes) == 1
