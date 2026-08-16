"""Black-Scholes Greeks formulas.

theta and vega are reported in the conventional trader-facing units, not
the raw textbook per-year / per-100%-vol derivatives: theta is scaled to
value change per calendar day (raw / 365), vega to value change per 1%
(0.01) change in volatility (raw / 100). Confirmed live against a real
2-day-to-expiry NIFTY option that the raw annualized theta (~-11,067) is
wildly misleading next to the real ~-30/day decay a trader would
recognize; every mainstream options platform (Zerodha, Sensibull,
Bloomberg) shows theta/vega in these scaled units. vanna/charm/vomma stay
in their raw textbook units -- vomma's formula needs vega's raw (per-100%)
form to be dimensionally correct, and none of the three have been
validated against a real-money reference the way theta/vega just were.
"""

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
    vega_raw = spot * growth * pdf_d1 * sqrt_t  # per 1.00 (100%) change in volatility
    vomma = vega_raw * d1 * d2 / volatility if volatility > 0 else 0.0
    vanna = -pdf_d1 * d2 / volatility if volatility > 0 else 0.0
    charm = -pdf_d1 * (
        (2 * (rate - dividend) * time_to_expiry - d2 * volatility * sqrt_t)
        / (2 * time_to_expiry * volatility * sqrt_t)
    ) * growth

    if contract.option_type == OptionType.CALL:
        delta = normal_cdf(d1) * growth
        theta_annual = (
            -spot * growth * pdf_d1 * volatility / (2 * sqrt_t)
            - rate * strike * discount * normal_cdf(d2)
            + dividend * spot * growth * normal_cdf(d1)
        )
        rho = strike * time_to_expiry * discount * normal_cdf(d2)
    else:
        delta = (normal_cdf(d1) - 1.0) * growth
        theta_annual = (
            -spot * growth * pdf_d1 * volatility / (2 * sqrt_t)
            + rate * strike * discount * normal_cdf(-d2)
            - dividend * spot * growth * normal_cdf(-d1)
        )
        rho = -strike * time_to_expiry * discount * normal_cdf(-d2)

    theta = theta_annual / 365.0  # per calendar day
    vega = vega_raw / 100.0  # per 1% (0.01) change in volatility

    scale = to_decimal(multiplier)
    return GreeksResult(
        delta=to_decimal(delta) * scale,
        gamma=to_decimal(gamma) * scale,
        # Scaled down (per-day / per-1%-vol) values are commonly sub-cent
        # before the lot-size multiplier; quantizing them at the same 4dp
        # as the other Greeks before multiplying would compound a rounding
        # error up by the multiplier, so keep more precision here.
        theta=to_decimal(theta, places="0.000001") * scale,
        vega=to_decimal(vega, places="0.000001") * scale,
        rho=to_decimal(rho) * scale,
        vanna=to_decimal(vanna) * scale,
        charm=to_decimal(charm) * scale,
        vomma=to_decimal(vomma) * scale,
        calculation_timestamp=datetime.now(timezone.utc),
        model_version=GreeksModelVersion.BLACK_SCHOLES_V1,
    )
