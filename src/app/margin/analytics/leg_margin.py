"""Per-leg margin calculation."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.payoff.models.legs import StrategyLeg

SPAN_PCT = Decimal("0.12")
EXPOSURE_PCT = Decimal("0.05")


def leg_notional(leg: StrategyLeg, context: CalculationContext) -> Decimal:
    """Return absolute notional for a leg."""
    strike = leg.strike if leg.strike > 0 else context.atm_strike
    return abs(Decimal(leg.quantity) * Decimal(leg.multiplier) * strike)


def leg_initial_margin(
    leg: StrategyLeg,
    context: CalculationContext,
) -> tuple[Decimal, Decimal, Decimal]:
    """Return initial, span, and exposure margin for one leg."""
    notional = leg_notional(leg, context)
    premium = abs(Decimal(leg.quantity) * Decimal(leg.multiplier) * leg.premium)
    if leg.quantity >= 0:
        return premium, Decimal("0"), Decimal("0")
    span = notional * SPAN_PCT
    exposure = notional * EXPOSURE_PCT
    initial = max(span + exposure, premium)
    return initial, span, exposure
