"""Margin utilization estimate."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.payoff.models.legs import StrategyLeg


def margin_utilization_estimate(
    legs: tuple[StrategyLeg, ...],
    context: CalculationContext,
    capital_at_risk: Decimal,
) -> Decimal:
    """Estimate margin utilization as fraction of notional."""
    notional = sum(
        abs(Decimal(leg.quantity) * Decimal(leg.multiplier) * leg.strike)
        for leg in legs
    )
    if notional == 0:
        return Decimal("0")
    margin_est = capital_at_risk * Decimal("1.5")
    return min(margin_est / notional, Decimal("1"))
