"""Unit test skeletons for subscription lifecycle."""

import pytest


@pytest.mark.skip(reason="Skeleton only")
def test_subscribe_queues_when_disconnected() -> None:
  """Subscribe should not call broker when disconnected."""
  assert True


@pytest.mark.skip(reason="Skeleton only")
def test_activate_pending_on_connect() -> None:
  """activate_pending should move symbols to active subscriptions."""
  assert True


@pytest.mark.skip(reason="Skeleton only")
def test_resubscribe_all_after_reconnect() -> None:
  """resubscribe_all should re-send broker subscriptions."""
  assert True
