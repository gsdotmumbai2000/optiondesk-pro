"""Cache key helpers."""

from app.calculation.context.calculation_context import CalculationContext
from app.pricing.models.option_contract import OptionContract


def build_cache_key(
    context: CalculationContext,
    contract: OptionContract,
) -> str:
    """Build cache key for Greeks analytics."""
    return (
        f"{context.exchange}:"
        f"{context.underlying}:"
        f"{contract.strike}:"
        f"{contract.option_type.value}:"
        f"{contract.expiry}:"
        f"{context.spot_price}"
    )
