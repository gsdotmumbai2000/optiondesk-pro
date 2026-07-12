"""Underlying provider."""

from dataclasses import dataclass


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
