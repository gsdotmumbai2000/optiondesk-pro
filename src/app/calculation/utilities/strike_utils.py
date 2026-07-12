"""Strike utility functions."""

from decimal import Decimal, ROUND_HALF_UP


def round_strike(price: Decimal, strike_interval: Decimal) -> Decimal:
    """Round price to nearest valid strike."""
    if strike_interval <= 0:
        return price
    steps = (price / strike_interval).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return steps * strike_interval


def atm_strike(spot: Decimal, strike_interval: Decimal) -> Decimal:
    """Return ATM strike."""
    return round_strike(spot, strike_interval)


def nearest_strike(price: Decimal, strike_interval: Decimal) -> Decimal:
    """Return nearest strike."""
    return round_strike(price, strike_interval)


def next_strike(price: Decimal, strike_interval: Decimal) -> Decimal:
    """Return next strike above price."""
    base = round_strike(price, strike_interval)
    if base <= price:
        return base + strike_interval
    return base


def previous_strike(price: Decimal, strike_interval: Decimal) -> Decimal:
    """Return previous strike below price."""
    base = round_strike(price, strike_interval)
    if base >= price:
        return base - strike_interval
    return base
