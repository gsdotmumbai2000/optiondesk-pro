"""Live market data unit test skeletons."""

import pytest

from app.market_data.live.tick_cache import TickCache
from app.market_data.live.tick_dispatcher import TickDispatcher
from app.tests.market_data.live.mock_tick_generator import MockTickGenerator


@pytest.mark.skip("Skeleton — implement tick cache tests")
def test_tick_cache_stores_latest() -> None:
    """TickCache should store and return latest tick."""
    cache = TickCache()
    tick = MockTickGenerator().next_tick()
    cache.put(tick)
    assert cache.get("NSE", "NIFTY") is not None


@pytest.mark.skip("Skeleton — implement duplicate tick protection")
def test_tick_dispatcher_skips_duplicates() -> None:
    """TickDispatcher should ignore duplicate ticks."""
    dispatcher = TickDispatcher(TickCache())
    tick = MockTickGenerator().next_tick()
    assert dispatcher.dispatch(tick) is True
    assert dispatcher.dispatch(tick) is False


@pytest.mark.skip("Skeleton — implement market data service API")
def test_market_data_service_latest_price() -> None:
    """MarketDataService.latest_price should read from TickCache."""
    pass


@pytest.mark.skip("Skeleton — implement subscription manager tests")
def test_subscription_manager_tracks_active() -> None:
    """Subscription manager should track active subscriptions."""
    pass
