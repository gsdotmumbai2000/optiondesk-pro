"""Live market data providers."""

__all__ = ["LiveMarketDataProvider", "MarketStatusDetector", "MarketStatusSnapshot"]


def __getattr__(name: str):
    """Lazy provider exports to avoid import cycles."""
    if name == "LiveMarketDataProvider":
        from app.market_data.providers.live_market_provider import LiveMarketDataProvider

        return LiveMarketDataProvider
    if name in {"MarketStatusDetector", "MarketStatusSnapshot"}:
        from app.market_data.providers import market_status_detector as module

        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
