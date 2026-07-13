"""Market data service bundle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.market_data.services.market_cache_service import MarketCacheService
from app.market_data.services.market_data_service import MarketDataService
from app.market_data.services.reconnect_service import ReconnectService
from app.market_data.subscriptions.subscription_service import SubscriptionService
from app.market_data.websocket.websocket_service import WebSocketService

if TYPE_CHECKING:
    from app.market_data.providers.live_market_provider import LiveMarketDataProvider


@dataclass(frozen=True, slots=True)
class MarketDataServiceBundle:
    """Enterprise market data services."""

    market_data: MarketDataService
    subscriptions: SubscriptionService
    websocket: WebSocketService
    reconnect: ReconnectService
    cache: MarketCacheService

    @classmethod
    def from_provider(cls, provider: LiveMarketDataProvider) -> MarketDataServiceBundle:
        """Build bundle from live provider."""
        return cls(
            market_data=provider.service,
            subscriptions=provider.subscriptions,
            websocket=provider.websocket,
            reconnect=provider.reconnect,
            cache=provider.cache,
        )
