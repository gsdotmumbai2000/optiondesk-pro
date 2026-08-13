"""Underlying provider."""

from dataclasses import dataclass

# An underlying's cash/index quote always lives on its cash exchange, never on
# whichever derivatives exchange a particular option contract belongs to.
# Confirmed against the application's Instrument Master, which already models
# an index (e.g. NIFTY on NSE) as a distinct instrument from its options (on
# NFO), sharing only the underlying symbol.
_CASH_EXCHANGE_FOR_DERIVATIVES: dict[str, str] = {
    "NFO": "NSE",
    "BFO": "BSE",
}


def cash_exchange_for(exchange: str) -> str:
    """Return the cash/spot exchange for a (possibly derivatives) exchange code.

    Unrecognized exchanges are returned unchanged.
    """
    return _CASH_EXCHANGE_FOR_DERIVATIVES.get(exchange.strip().upper(), exchange)


@dataclass(frozen=True, slots=True)
class UnderlyingInfo:
    """Resolved underlying metadata."""

    underlying: str
    underlying_symbol: str
    exchange: str
    currency: str = "INR"


class UnderlyingProvider:
    """Resolve underlying metadata."""

    def resolve(self, underlying: str, exchange: str) -> UnderlyingInfo:
        """Return underlying info."""
        symbol = underlying.upper()
        return UnderlyingInfo(
            underlying=symbol,
            underlying_symbol=symbol,
            exchange=exchange.upper(),
        )
