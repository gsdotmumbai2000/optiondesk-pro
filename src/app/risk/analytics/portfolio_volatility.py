"""Portfolio volatility estimation."""

from decimal import Decimal

from app.volatility.models.volatility_result import VolatilityResult


def portfolio_volatility(
    volatility: VolatilityResult,
    net_delta: Decimal,
) -> Decimal:
    """Estimate portfolio volatility from IV and delta exposure."""
    iv = volatility.annualized_volatility
    delta_weight = abs(net_delta) if net_delta != 0 else Decimal("1")
    return iv * (Decimal("1") + delta_weight * Decimal("0.1"))
