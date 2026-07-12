"""Connection status service tests."""

import pytest

from app.brokers.shared.enums import BrokerConnectionStatus, ConnectionState
from app.config.models.app_config import BrokerConfig
from app.services.broker.connection_status_service import ConnectionStatusService


@pytest.mark.skip("Skeleton — implement status mapping")
def test_maps_connected_state() -> None:
    """Service should map CONNECTED to Connected status label."""
    service = ConnectionStatusService(BrokerConfig())
    snap = service.update_state(ConnectionState.CONNECTED, session_valid=True)
    assert snap.status == BrokerConnectionStatus.CONNECTED


@pytest.mark.skip("Skeleton — implement auth failed mapping")
def test_maps_authentication_failed() -> None:
    """Service should map AUTHENTICATION_FAILED to Authentication Failed."""
    pass
