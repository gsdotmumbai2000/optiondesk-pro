"""Strike price utilities."""

from decimal import ROUND_HALF_UP, Decimal


def round_strike(price: Decimal, strike_interval: Decimal) -> Decimal:
    """Round a price to the nearest valid strike."""
    if strike_interval <= 0:
        return price
    steps = (price / strike_interval).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return steps * strike_interval


def nearest_strike(price: Decimal, strike_interval: Decimal) -> Decimal:
    """Return the nearest strike to a price."""
    return round_strike(price, strike_interval)


def next_strike(price: Decimal, strike_interval: Decimal) -> Decimal:
    """Return the next strike above price."""
    base = round_strike(price, strike_interval)
    if base <= price:
        return base + strike_interval
    return base


def previous_strike(price: Decimal, strike_interval: Decimal) -> Decimal:
    """Return the previous strike below price."""
    base = round_strike(price, strike_interval)
    if base >= price:
        return base - strike_interval
    return base


def atm_strike(spot: Decimal, strike_interval: Decimal) -> Decimal:
    """Return the at-the-money strike."""
    return nearest_strike(spot, strike_interval)


def otm_strike(
    spot: Decimal,
    strike_interval: Decimal,
    *,
    option_right: str,
) -> Decimal:
    """Return a one-step out-of-the-money strike."""
    right = option_right.upper()
    if right == "CE":
        return next_strike(spot, strike_interval)
    return previous_strike(spot, strike_interval)


def itm_strike(
    spot: Decimal,
    strike_interval: Decimal,
    *,
    option_right: str,
) -> Decimal:
    """Return a one-step in-the-money strike."""
    right = option_right.upper()
    if right == "CE":
        return previous_strike(spot, strike_interval)
    return next_strike(spot, strike_interval)
