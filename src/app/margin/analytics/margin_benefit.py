"""Margin benefit and offset calculation."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.margin.analytics.leg_margin import leg_notional
from app.payoff.models.legs import StrategyLeg
from app.pricing.models.enums import OptionType


def margin_benefit(
    legs: tuple[StrategyLeg, ...],
    context: CalculationContext,
) -> Decimal:
    """Estimate margin offset from hedged positions."""
    calls_short = Decimal("0")
    calls_long = Decimal("0")
    puts_short = Decimal("0")
    puts_long = Decimal("0")
    for leg in legs:
        n = leg_notional(leg, context)
        if leg.option_type == OptionType.CALL:
            if leg.quantity < 0:
                calls_short += n
            else:
                calls_long += n
        else:
            if leg.quantity < 0:
                puts_short += n
            else:
                puts_long += n
    hedge_offset = min(calls_short, calls_long) + min(puts_short, puts_long)
    return hedge_offset * Decimal("0.25")
