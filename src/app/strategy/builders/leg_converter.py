"""Convert strategy legs to payoff engine legs."""

from datetime import date
from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.payoff.models.legs import StrategyLeg as PayoffLeg
from app.pricing.models.enums import OptionType
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg


def to_payoff_legs(
    legs: tuple[StrategyLeg, ...],
    context: CalculationContext,
) -> tuple[PayoffLeg, ...]:
    """Convert strategy legs to payoff engine legs."""
    result: list[PayoffLeg] = []
    for leg in legs:
        converted = _convert_leg(leg, context)
        if converted is not None:
            result.append(converted)
    return tuple(result)


def _convert_leg(
    leg: StrategyLeg,
    context: CalculationContext,
) -> PayoffLeg | None:
    option_type, quantity = _resolve_option(leg)
    if option_type is None:
        return None
    strike = leg.strike if leg.strike > 0 else context.atm_strike
    expiry = leg.expiry or context.expiry
    return PayoffLeg(
        strike=strike,
        option_type=option_type,
        quantity=quantity,
        premium=leg.premium,
        expiry=expiry,
        multiplier=leg.multiplier,
        underlying=leg.underlying or context.underlying,
        exchange=leg.exchange or context.exchange,
    )


def _resolve_option(leg: StrategyLeg) -> tuple[OptionType | None, int]:
    mapping: dict[LegKind, tuple[OptionType, int]] = {
        LegKind.CALL_BUY: (OptionType.CALL, abs(leg.quantity)),
        LegKind.CALL_SELL: (OptionType.CALL, -abs(leg.quantity)),
        LegKind.PUT_BUY: (OptionType.PUT, abs(leg.quantity)),
        LegKind.PUT_SELL: (OptionType.PUT, -abs(leg.quantity)),
        LegKind.FUTURE_BUY: (OptionType.CALL, abs(leg.quantity)),
        LegKind.FUTURE_SELL: (OptionType.PUT, -abs(leg.quantity)),
        LegKind.STOCK_BUY: (OptionType.CALL, abs(leg.quantity)),
        LegKind.STOCK_SELL: (OptionType.PUT, -abs(leg.quantity)),
    }
    resolved = mapping.get(leg.kind)
    if resolved is None:
        return None, 0
    return resolved
