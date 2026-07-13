"""Live market data backward compatibility."""

__all__ = [
    "LiveMarketDataProvider",
    "MarketDataSubscriptionManager",
    "TickCache",
    "TickDispatcher",
    "WebSocketManager",
]


def __getattr__(name: str):
    """Lazy exports to avoid import cycles."""
    if name == "LiveMarketDataProvider":
        from app.market_data.live.live_provider import LiveMarketDataProvider

        return LiveMarketDataProvider
    if name == "MarketDataSubscriptionManager":
        from app.market_data.live.subscription_manager import MarketDataSubscriptionManager

        return MarketDataSubscriptionManager
    if name == "TickCache":
        from app.market_data.live.tick_cache import TickCache

        return TickCache
    if name == "TickDispatcher":
        from app.market_data.live.tick_dispatcher import TickDispatcher

        return TickDispatcher
    if name == "WebSocketManager":
        from app.market_data.live.websocket_manager import WebSocketManager

        return WebSocketManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
