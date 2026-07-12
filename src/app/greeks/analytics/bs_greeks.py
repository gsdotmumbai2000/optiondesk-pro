"""Black-Scholes Greeks formulas."""

import math

from app.calculation.context.calculation_context import CalculationContext
from app.greeks.models.enums import GreeksModelVersion
from app.greeks.models.greeks_result import GreeksResult
from app.pricing.black_scholes.distribution import normal_cdf, normal_pdf
from app.pricing.models.enums import OptionType
from app.pricing.models.option_contract import OptionContract
from app.pricing.models.pricing_result import PricingResult
from app.pricing.utilities.decimal_utils import to_decimal, to_float


def calculate_bs_greeks(
    context: CalculationContext,
    contract: OptionContract,
    pricing_result: PricingResult,
) -> GreeksResult:
    """Compute European option Greeks from pricing intermediates."""
    from datetime import datetime, timezone

    spot = to_float(context.spot_price)
    strike = to_float(contract.strike)
    time_to_expiry = to_float(context.time_to_expiry)
    rate = to_float(context.risk_free_rate)
    dividend = to_float(context.dividend_yield)
    volatility = to_float(context.volatility)
    d1 = to_float(pricing_result.d1)
    d2 = to_float(pricing_result.d2)
    multiplier = to_float(contract.multiplier)

    if time_to_expiry <= 0.0 or volatility <= 0.0 or spot <= 0.0:
        zero = to_decimal(0.0)
        return GreeksResult(
            delta=zero,
            gamma=zero,
            theta=zero,
            vega=zero,
            rho=zero,
            vanna=zero,
            charm=zero,
            vomma=zero,
            calculation_timestamp=datetime.now(timezone.utc),
            model_version=GreeksModelVersion.BLACK_SCHOLES_V1,
        )

    pdf_d1 = normal_pdf(d1)
    sqrt_t = math.sqrt(time_to_expiry)
    growth = math.exp(-dividend * time_to_expiry)
    discount = math.exp(-rate * time_to_expiry)

    gamma = pdf_d1 / (spot * volatility * sqrt_t) * growth
    vega = spot * growth * pdf_d1 * sqrt_t
    vomma = vega * d1 * d2 / volatility if volatility > 0 else 0.0
    vanna = -pdf_d1 * d2 / volatility if volatility > 0 else 0.0
    charm = -pdf_d1 * (
        (2 * (rate - dividend) * time_to_expiry - d2 * volatility * sqrt_t)
        / (2 * time_to_expiry * volatility * sqrt_t)
    ) * growth

    if contract.option_type == OptionType.CALL:
        delta = normal_cdf(d1) * growth
        theta = (
            -spot * growth * pdf_d1 * volatility / (2 * sqrt_t)
            - rate * strike * discount * normal_cdf(d2)
            + dividend * spot * growth * normal_cdf(d1)
        )
        rho = strike * time_to_expiry * discount * normal_cdf(d2)
    else:
        delta = (normal_cdf(d1) - 1.0) * growth
        theta = (
            -spot * growth * pdf_d1 * volatility / (2 * sqrt_t)
            + rate * strike * discount * normal_cdf(-d2)
            - dividend * spot * growth * normal_cdf(-d1)
        )
        rho = -strike * time_to_expiry * discount * normal_cdf(-d2)

    scale = to_decimal(multiplier)
    return GreeksResult(
        delta=to_decimal(delta) * scale,
        gamma=to_decimal(gamma) * scale,
        theta=to_decimal(theta) * scale,
        vega=to_decimal(vega) * scale,
        rho=to_decimal(rho) * scale,
        vanna=to_decimal(vanna) * scale,
        charm=to_decimal(charm) * scale,
        vomma=to_decimal(vomma) * scale,
        calculation_timestamp=datetime.now(timezone.utc),
        model_version=GreeksModelVersion.BLACK_SCHOLES_V1,
    )
