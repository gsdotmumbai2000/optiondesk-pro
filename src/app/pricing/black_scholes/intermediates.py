"""Reusable Black-Scholes intermediate values."""

import math
from dataclasses import dataclass

from app.calculation.context.calculation_context import CalculationContext
from app.pricing.black_scholes import formulas
from app.pricing.utilities.decimal_utils import to_float


@dataclass(frozen=True, slots=True)
class BSContextTerms:
    """Strike-independent terms derived from calculation context."""

    spot: float
    rate: float
    dividend_yield: float
    volatility: float
    time_to_expiry: float
    discount_factor: float
    forward_price: float
    vol_sqrt_time: float

    @classmethod
    def from_context(cls, context: CalculationContext) -> "BSContextTerms":
        """Build reusable context terms."""
        spot = to_float(context.spot_price)
        rate = to_float(context.risk_free_rate)
        dividend = to_float(context.dividend_yield)
        volatility = to_float(context.volatility)
        time_to_expiry = to_float(context.time_to_expiry)
        discount = formulas.discount_factor(rate, time_to_expiry)
        forward = formulas.forward_price(spot, rate, dividend, time_to_expiry)
        vol_sqrt_time = volatility * math.sqrt(time_to_expiry)
        return cls(
            spot=spot,
            rate=rate,
            dividend_yield=dividend,
            volatility=volatility,
            time_to_expiry=time_to_expiry,
            discount_factor=discount,
            forward_price=forward,
            vol_sqrt_time=vol_sqrt_time,
        )


@dataclass(frozen=True, slots=True)
class BSStrikeTerms:
    """Strike-specific Black-Scholes intermediates."""

    strike: float
    d1: float
    d2: float

    @classmethod
    def from_context_terms(
        cls,
        terms: BSContextTerms,
        strike: float,
    ) -> "BSStrikeTerms":
        """Build strike-specific terms from context terms."""
        d1_value = formulas.d1(
            terms.spot,
            strike,
            terms.rate,
            terms.dividend_yield,
            terms.volatility,
            terms.time_to_expiry,
        )
        d2_value = formulas.d2(d1_value, terms.volatility, terms.time_to_expiry)
        return cls(strike=strike, d1=d1_value, d2=d2_value)
