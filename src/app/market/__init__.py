"""Market Master package."""

from typing import Any

__all__ = ["MarketCache", "MarketMasterProvider", "InstrumentService"]


def __getattr__(name: str) -> Any:
    """Lazy exports to avoid import cycles."""
    if name == "MarketMasterProvider":
        from app.market.bootstrap import MarketMasterProvider

        return MarketMasterProvider
    if name == "MarketCache":
        from app.market.cache.market_cache import MarketCache

        return MarketCache
    if name == "InstrumentService":
        from app.market.instrument_master.service import InstrumentService

        return InstrumentService
    raise AttributeError(name)
