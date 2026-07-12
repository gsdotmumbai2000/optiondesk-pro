"""Probability of profit analytics."""

from decimal import Decimal

from app.pricing.black_scholes.distribution import normal_cdf
from app.pricing.models.enums import OptionType
from app.pricing.models.option_contract import OptionContract
from app.pricing.models.pricing_result import PricingResult
from app.pricing.utilities.decimal_utils import to_float


def probability_of_profit(
    pricing_result: PricingResult,
    contract: OptionContract | None = None,
) -> Decimal:
    """Estimate probability of profit using risk-neutral distribution."""
    d2 = to_float(pricing_result.d2)
    if contract is not None and contract.option_type == OptionType.PUT:
        return Decimal(str(normal_cdf(-d2)))
    return Decimal(str(normal_cdf(d2)))
