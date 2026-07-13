"""Live market data unit test skeletons."""

import pytest

from app.market_data.cache.live_tick_cache import LiveTickCache
from app.market_data.dispatcher.event_dispatcher import EventDispatcher
from app.market_data.services.market_cache_service import MarketCacheService
from app.tests.market_data.live.mock_tick_generator import MockTickGenerator


@pytest.mark.skip("Skeleton — implement tick cache tests")
def test_tick_cache_stores_latest() -> None:
    """LiveTickCache should store and return latest tick."""
    cache = LiveTickCache()
    tick = MockTickGenerator().next_tick()
    cache.put(tick)
    assert cache.get("NSE", "NIFTY") is not None


@pytest.mark.skip("Skeleton — implement duplicate tick protection")
def test_tick_dispatcher_skips_duplicates() -> None:
    """EventDispatcher should ignore duplicate ticks."""
    cache = MarketCacheService()
    dispatcher = EventDispatcher(cache, can_dispatch=lambda: True)
    tick = MockTickGenerator().next_tick()
    assert dispatcher.dispatch(tick) is True
    assert dispatcher.dispatch(tick) is False
    dispatcher.shutdown()


@pytest.mark.skip("Skeleton — implement market data service API")
def test_market_data_service_latest_price() -> None:
    """MarketDataService.latest_price should read from MarketCacheService."""
    pass


@pytest.mark.skip("Skeleton — implement connection state gating")
def test_subscriptions_pending_until_connected() -> None:
    """Subscriptions must remain pending until BrokerConnected."""
    pass


@pytest.mark.skip("Skeleton — implement disconnect retains watchlist")
def test_disconnect_keeps_pending_watchlist() -> None:
    """BrokerDisconnected should deactivate broker subs but keep pending."""
    pass
