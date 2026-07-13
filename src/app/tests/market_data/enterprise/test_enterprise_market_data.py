"""Unit test skeletons for enterprise live market data engine."""

import pytest


@pytest.mark.skip(reason="Skeleton only — implement with mocked broker")
def test_live_engine_starts_and_stops() -> None:
  """LiveMarketDataEngine should start without broker subscriptions."""
  assert True


@pytest.mark.skip(reason="Skeleton only")
def test_market_data_service_latest_price() -> None:
  """MarketDataService should return None when symbol not cached."""
  assert True


@pytest.mark.skip(reason="Skeleton only")
def test_subscription_service_bulk_subscribe() -> None:
  """SubscriptionService should queue bulk symbols as pending."""
  assert True


@pytest.mark.skip(reason="Skeleton only")
def test_event_dispatcher_publishes_price_updated() -> None:
  """EventDispatcher should publish PriceUpdatedEvent on tick."""
  assert True


@pytest.mark.skip(reason="Skeleton only")
def test_reconnect_service_exponential_backoff() -> None:
  """ReconnectService should increase delay between attempts."""
  assert True


@pytest.mark.skip(reason="Skeleton only")
def test_market_cache_service_lru_expiration() -> None:
  """MarketCacheService should purge expired ticks."""
  assert True


@pytest.mark.skip(reason="Skeleton only")
def test_connection_state_machine_gates_subscriptions() -> None:
  """Subscriptions should not activate when disconnected."""
  assert True
