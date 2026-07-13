"""Market data services package."""

__all__ = [
    "MarketCacheService",
    "MarketDataService",
    "MarketDataServiceBundle",
    "ReconnectService",
    "SubscriptionService",
    "WebSocketService",
]


def __getattr__(name: str):
    """Lazy service exports to avoid import cycles."""
    if name == "MarketCacheService":
        from app.market_data.services.market_cache_service import MarketCacheService

        return MarketCacheService
    if name == "MarketDataService":
        from app.market_data.services.market_data_service import MarketDataService

        return MarketDataService
    if name == "MarketDataServiceBundle":
        from app.market_data.services.bundle import MarketDataServiceBundle

        return MarketDataServiceBundle
    if name == "ReconnectService":
        from app.market_data.services.reconnect_service import ReconnectService

        return ReconnectService
    if name == "SubscriptionService":
        from app.market_data.services.subscription_service import SubscriptionService

        return SubscriptionService
    if name == "WebSocketService":
        from app.market_data.services.websocket_service import WebSocketService

        return WebSocketService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
