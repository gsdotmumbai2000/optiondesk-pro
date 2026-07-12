"""Portfolio beta estimation."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.greeks.models.greeks_result import GreeksResult


def portfolio_beta(
    context: CalculationContext,
    greeks: GreeksResult,
    net_delta: Decimal,
) -> Decimal:
    """Estimate portfolio beta from delta exposure and spot."""
    if context.spot_price <= 0:
        return Decimal("0")
    return net_delta * greeks.delta / context.spot_price
