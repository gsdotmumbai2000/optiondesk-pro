"""Implied volatility solver (Black-Scholes inversion)."""

from app.pricing.black_scholes import formulas
from app.pricing.models.enums import OptionType

_MIN_VOLATILITY = 1e-4
_MAX_VOLATILITY = 5.0


def _price_at(
    volatility: float,
    spot: float,
    strike: float,
    rate: float,
    dividend_yield: float,
    time_to_expiry: float,
    option_type: OptionType,
) -> float:
    d1_value = formulas.d1(spot, strike, rate, dividend_yield, volatility, time_to_expiry)
    d2_value = formulas.d2(d1_value, volatility, time_to_expiry)
    if option_type == OptionType.CALL:
        return formulas.call_price(spot, strike, rate, dividend_yield, time_to_expiry, d1_value, d2_value)
    return formulas.put_price(spot, strike, rate, dividend_yield, time_to_expiry, d1_value, d2_value)


def implied_volatility(
    market_price: float,
    spot: float,
    strike: float,
    rate: float,
    dividend_yield: float,
    time_to_expiry: float,
    option_type: OptionType,
    *,
    tolerance: float = 1e-6,
    max_iterations: int = 100,
) -> float | None:
    """Solve for volatility such that the Black-Scholes price matches
    `market_price`, via bisection on [_MIN_VOLATILITY, _MAX_VOLATILITY].

    Call/put price is monotonically increasing in volatility for
    time_to_expiry > 0, so bisection always converges. Returns None when
    inputs are unusable (non-positive price/spot/strike/time) or when
    `market_price` falls outside the price range spanned by that volatility
    bracket (stale/crossed/bad quote -- no solution exists in-range).
    """
    if time_to_expiry <= 0.0 or spot <= 0.0 or strike <= 0.0 or market_price <= 0.0:
        return None

    low, high = _MIN_VOLATILITY, _MAX_VOLATILITY
    price_low = _price_at(low, spot, strike, rate, dividend_yield, time_to_expiry, option_type)
    price_high = _price_at(high, spot, strike, rate, dividend_yield, time_to_expiry, option_type)
    if market_price <= price_low or market_price >= price_high:
        return None

    mid = (low + high) / 2.0
    for _ in range(max_iterations):
        if high - low < tolerance:
            break
        mid = (low + high) / 2.0
        price_mid = _price_at(mid, spot, strike, rate, dividend_yield, time_to_expiry, option_type)
        if price_mid > market_price:
            high = mid
        else:
            low = mid
    return (low + high) / 2.0
