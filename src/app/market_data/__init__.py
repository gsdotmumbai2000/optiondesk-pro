"""Market data engine package."""

__all__ = ["MarketDataEngine", "MarketDataProvider"]


def __getattr__(name: str) -> object:
    """Lazy exports."""
    if name == "MarketDataEngine":
        from app.market_data.engine.market_data_engine import MarketDataEngine

        return MarketDataEngine
    if name == "MarketDataProvider":
        from app.market_data.bootstrap import MarketDataProvider

        return MarketDataProvider
    raise AttributeError(name)
