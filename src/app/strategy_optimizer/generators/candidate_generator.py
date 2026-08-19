"""Candidate strategy generators."""

from datetime import date
from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.strategy.models.enums import LegKind, StrategyType
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.metadata import StrategyMetadata
from app.strategy.models.strategy import Strategy
from app.strategy.templates.builtin import get_builtin_templates
from app.utils.uuid_helper import generate_uuid

_SINGLE_LEG_SWEEP_RADIUS = 10  # strike offsets either side of ATM, in steps
_SPREAD_WIDTHS = range(1, 9)  # vertical spread widths, in steps
_STRANGLE_WIDTHS = range(1, 7)
_CONDOR_INNER_WIDTHS = range(1, 5)
_CONDOR_OUTER_OFFSETS = range(1, 4)


def _leg(
    kind: LegKind,
    strike: Decimal,
    expiry: date,
    qty: int = 1,
) -> StrategyLeg:
    return StrategyLeg(
        leg_id=generate_uuid(),
        kind=kind,
        quantity=qty,
        premium=Decimal("0"),
        strike=strike,
        expiry=expiry,
    )


def _strategy(name: str, stype: StrategyType, legs: tuple[StrategyLeg, ...]) -> Strategy:
    return Strategy(
        metadata=StrategyMetadata(
            strategy_id=generate_uuid(),
            name=name,
            recognized_type=stype,
        ),
        legs=legs,
    )


class CandidateGenerator:
    """Generate candidate strategies from search space."""

    def generate(self, context: CalculationContext) -> tuple[Strategy, ...]:
        """Generate candidates for underlying and expiry: named templates
        plus a real strike/width sweep (single legs across a strike window,
        spreads/strangles/condors across several widths) so search
        algorithms have an actual space to search rather than a handful of
        fixed-strike strategies."""
        expiry = context.expiry
        atm = context.atm_strike
        step = context.strike_interval
        candidates: list[Strategy] = []
        candidates.extend(self._from_templates(expiry, atm))
        candidates.extend(self._single_legs(expiry, atm, step))
        candidates.extend(self._vertical_spreads(expiry, atm, step))
        candidates.extend(self._straddles_strangles(expiry, atm, step))
        return tuple(candidates)

    def _from_templates(self, expiry: date, atm: Decimal) -> list[Strategy]:
        result: list[Strategy] = []
        for tmpl in get_builtin_templates():
            legs = tuple(
                StrategyLeg(
                    leg_id=generate_uuid(),
                    kind=leg.kind,
                    quantity=leg.quantity,
                    premium=leg.premium,
                    strike=atm if leg.strike == Decimal("0") else leg.strike,
                    expiry=expiry,
                    multiplier=leg.multiplier,
                )
                for leg in tmpl.legs
            )
            result.append(
                _strategy(tmpl.name, tmpl.strategy_type, legs)
            )
        return result

    def _single_legs(self, expiry: date, atm: Decimal, step: Decimal) -> list[Strategy]:
        kinds = (
            ("Long Call", StrategyType.LONG_CALL, LegKind.CALL_BUY),
            ("Long Put", StrategyType.LONG_PUT, LegKind.PUT_BUY),
            ("Short Call", StrategyType.SHORT_CALL, LegKind.CALL_SELL),
            ("Short Put", StrategyType.SHORT_PUT, LegKind.PUT_SELL),
        )
        result: list[Strategy] = []
        for offset in range(-_SINGLE_LEG_SWEEP_RADIUS, _SINGLE_LEG_SWEEP_RADIUS + 1):
            strike = atm + step * offset
            if strike <= 0:
                continue
            for name, stype, kind in kinds:
                result.append(_strategy(f"{name} {strike}", stype, (_leg(kind, strike, expiry),)))
        return result

    def _vertical_spreads(
        self, expiry: date, atm: Decimal, step: Decimal
    ) -> list[Strategy]:
        result: list[Strategy] = []
        for width in _SPREAD_WIDTHS:
            upper = atm + step * width
            lower = atm - step * width
            if lower <= 0:
                continue
            result.append(
                _strategy(
                    f"Bull Call Spread {lower}/{upper}",
                    StrategyType.BULL_CALL_SPREAD,
                    (_leg(LegKind.CALL_BUY, lower, expiry), _leg(LegKind.CALL_SELL, upper, expiry)),
                )
            )
            result.append(
                _strategy(
                    f"Bear Put Spread {lower}/{upper}",
                    StrategyType.BEAR_PUT_SPREAD,
                    (_leg(LegKind.PUT_BUY, upper, expiry), _leg(LegKind.PUT_SELL, lower, expiry)),
                )
            )
        return result

    def _straddles_strangles(
        self, expiry: date, atm: Decimal, step: Decimal
    ) -> list[Strategy]:
        result: list[Strategy] = [
            _strategy(
                "Long Straddle",
                StrategyType.LONG_STRADDLE,
                (_leg(LegKind.CALL_BUY, atm, expiry), _leg(LegKind.PUT_BUY, atm, expiry)),
            ),
        ]
        for width in _STRANGLE_WIDTHS:
            call_strike = atm + step * width
            put_strike = atm - step * width
            if put_strike <= 0:
                continue
            result.append(
                _strategy(
                    f"Long Strangle {put_strike}/{call_strike}",
                    StrategyType.LONG_STRANGLE,
                    (_leg(LegKind.CALL_BUY, call_strike, expiry), _leg(LegKind.PUT_BUY, put_strike, expiry)),
                )
            )
        for inner in _CONDOR_INNER_WIDTHS:
            for outer_offset in _CONDOR_OUTER_OFFSETS:
                outer = inner + outer_offset
                put_buy = atm - step * outer
                put_sell = atm - step * inner
                call_sell = atm + step * inner
                call_buy = atm + step * outer
                if put_buy <= 0:
                    continue
                result.append(
                    _strategy(
                        f"Iron Condor {inner}/{outer}",
                        StrategyType.IRON_CONDOR,
                        (
                            _leg(LegKind.PUT_BUY, put_buy, expiry),
                            _leg(LegKind.PUT_SELL, put_sell, expiry),
                            _leg(LegKind.CALL_SELL, call_sell, expiry),
                            _leg(LegKind.CALL_BUY, call_buy, expiry),
                        ),
                    )
                )
        return result
