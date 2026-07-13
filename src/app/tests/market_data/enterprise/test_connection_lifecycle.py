"""Unit test skeletons for connection lifecycle."""

import pytest


@pytest.mark.skip(reason="Skeleton only")
def test_connection_established_event_on_broker_connect() -> None:
  """ConnectionStateMachine should publish ConnectionEstablishedEvent."""
  assert True


@pytest.mark.skip(reason="Skeleton only")
def test_connection_lost_event_on_broker_disconnect() -> None:
  """ConnectionStateMachine should publish ConnectionLostEvent."""
  assert True


@pytest.mark.skip(reason="Skeleton only")
def test_heartbeat_detects_stale_feed() -> None:
  """HeartbeatMonitor should flag stale websocket feed."""
  assert True
