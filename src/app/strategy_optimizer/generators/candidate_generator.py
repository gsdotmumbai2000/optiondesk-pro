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
        """Generate candidates for underlying and expiry."""
        expiry = context.expiry
        atm = context.atm_strike
        step = context.strike_interval
        candidates: list[Strategy] = []
        candidates.extend(self._from_templates(expiry, atm))
        candidates.extend(self._single_legs(expiry, atm))
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

    def _single_legs(self, expiry: date, atm: Decimal) -> list[Strategy]:
        return [
            _strategy("Long Call", StrategyType.LONG_CALL, (_leg(LegKind.CALL_BUY, atm, expiry),)),
            _strategy("Long Put", StrategyType.LONG_PUT, (_leg(LegKind.PUT_BUY, atm, expiry),)),
            _strategy("Short Call", StrategyType.SHORT_CALL, (_leg(LegKind.CALL_SELL, atm, expiry),)),
            _strategy("Short Put", StrategyType.SHORT_PUT, (_leg(LegKind.PUT_SELL, atm, expiry),)),
        ]

    def _vertical_spreads(
        self, expiry: date, atm: Decimal, step: Decimal
    ) -> list[Strategy]:
        upper = atm + step
        lower = atm - step
        return [
            _strategy(
                "Bull Call Spread",
                StrategyType.BULL_CALL_SPREAD,
                (_leg(LegKind.CALL_BUY, lower, expiry), _leg(LegKind.CALL_SELL, upper, expiry)),
            ),
            _strategy(
                "Bear Put Spread",
                StrategyType.BEAR_PUT_SPREAD,
                (_leg(LegKind.PUT_BUY, upper, expiry), _leg(LegKind.PUT_SELL, lower, expiry)),
            ),
        ]

    def _straddles_strangles(
        self, expiry: date, atm: Decimal, step: Decimal
    ) -> list[Strategy]:
        return [
            _strategy(
                "Long Straddle",
                StrategyType.LONG_STRADDLE,
                (_leg(LegKind.CALL_BUY, atm, expiry), _leg(LegKind.PUT_BUY, atm, expiry)),
            ),
            _strategy(
                "Long Strangle",
                StrategyType.LONG_STRANGLE,
                (
                    _leg(LegKind.CALL_BUY, atm + step, expiry),
                    _leg(LegKind.PUT_BUY, atm - step, expiry),
                ),
            ),
            _strategy(
                "Iron Condor",
                StrategyType.IRON_CONDOR,
                (
                    _leg(LegKind.PUT_BUY, atm - step * 2, expiry),
                    _leg(LegKind.PUT_SELL, atm - step, expiry),
                    _leg(LegKind.CALL_SELL, atm + step, expiry),
                    _leg(LegKind.CALL_BUY, atm + step * 2, expiry),
                ),
            ),
        ]
