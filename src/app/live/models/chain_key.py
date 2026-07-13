"""Live analytics chain key."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChainKey:
    """Canonical live chain identity."""

    underlying: str
    exchange: str
    expiry_date: str

    def cache_key(self) -> str:
        """Return cache lookup key."""
        return f"{self.exchange}:{self.underlying}:{self.expiry_date}"
