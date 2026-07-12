"""Black-Scholes core formulas."""

import math

from app.pricing.black_scholes.distribution import normal_cdf


def discount_factor(rate: float, time_to_expiry: float) -> float:
    """Return continuous discount factor exp(-rT)."""
    return math.exp(-rate * time_to_expiry)


def forward_price(
    spot: float,
    rate: float,
    dividend_yield: float,
    time_to_expiry: float,
) -> float:
    """Return forward price F = S * exp((r - q) * T)."""
    return spot * math.exp((rate - dividend_yield) * time_to_expiry)


def d1(
    spot: float,
    strike: float,
    rate: float,
    dividend_yield: float,
    volatility: float,
    time_to_expiry: float,
) -> float:
    """Return Black-Scholes d1."""
    if time_to_expiry <= 0.0 or volatility <= 0.0:
        return 0.0
    vol_sqrt_t = volatility * math.sqrt(time_to_expiry)
    numerator = math.log(spot / strike)
    numerator += (rate - dividend_yield + 0.5 * volatility * volatility) * time_to_expiry
    return numerator / vol_sqrt_t


def d2(d1_value: float, volatility: float, time_to_expiry: float) -> float:
    """Return Black-Scholes d2."""
    return d1_value - volatility * math.sqrt(time_to_expiry)


def call_price(
    spot: float,
    strike: float,
    rate: float,
    dividend_yield: float,
    time_to_expiry: float,
    d1_value: float,
    d2_value: float,
) -> float:
    """Return European call price."""
    growth = math.exp(-dividend_yield * time_to_expiry)
    discount = discount_factor(rate, time_to_expiry)
    return spot * growth * normal_cdf(d1_value) - strike * discount * normal_cdf(d2_value)


def put_price(
    spot: float,
    strike: float,
    rate: float,
    dividend_yield: float,
    time_to_expiry: float,
    d1_value: float,
    d2_value: float,
) -> float:
    """Return European put price."""
    growth = math.exp(-dividend_yield * time_to_expiry)
    discount = discount_factor(rate, time_to_expiry)
    return strike * discount * normal_cdf(-d2_value) - spot * growth * normal_cdf(-d1_value)
