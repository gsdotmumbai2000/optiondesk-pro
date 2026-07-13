"""Market data engine package."""

__all__ = ["LiveMarketDataEngine", "MarketDataEngine"]


def __getattr__(name: str):
    """Lazy engine exports to avoid import cycles."""
    if name == "LiveMarketDataEngine":
        from app.market_data.engine.live_engine import LiveMarketDataEngine

        return LiveMarketDataEngine
    if name == "MarketDataEngine":
        from app.market_data.engine.market_data_engine import MarketDataEngine

        return MarketDataEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
