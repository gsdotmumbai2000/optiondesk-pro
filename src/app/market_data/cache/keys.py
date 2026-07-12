"""Cache key helpers."""

from decimal import Decimal


def quote_key(
    exchange: str,
    symbol: str,
    *,
    expiry_date: str = "",
    strike_price: str | Decimal = "",
    option_right: str = "",
) -> str:
    """Build a canonical quote cache key."""
    strike = str(strike_price) if strike_price else ""
    return ":".join(
        [
            exchange.upper(),
            symbol.upper(),
            expiry_date,
            strike,
            option_right.upper(),
        ]
    )


def chain_key(underlying: str, exchange: str, expiry_date: str) -> str:
    """Build a canonical option chain cache key."""
    return f"{exchange.upper()}:{underlying.upper()}:{expiry_date}"
