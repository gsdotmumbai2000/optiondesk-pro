"""Broker factory and manager tests."""

import pytest

from app.brokers.bootstrap import BrokerProvider
from app.brokers.broker_factory.factory import BrokerFactory
from app.brokers.shared.enums import BrokerCode
from app.brokers.shared.exceptions import BrokerNotSupportedException
from app.config.models.app_config import BrokerConfig
from app.events.event_bus import EventBus
from app.security.credential_manager import CredentialManager


def test_factory_creates_breeze(
    broker_config: BrokerConfig,
    credential_manager: CredentialManager,
    mock_client_factory: object,
) -> None:
    """Factory should create Breeze broker."""
    factory = BrokerFactory(
        broker_config,
        credential_manager,
        EventBus(),
        client_factory=mock_client_factory,  # type: ignore[arg-type]
    )
    broker = factory.create()
    assert broker.broker_code == BrokerCode.BREEZE


def test_factory_rejects_unknown_broker(
    broker_config: BrokerConfig,
    credential_manager: CredentialManager,
) -> None:
    """Factory should reject unsupported brokers."""
    factory = BrokerFactory(broker_config, credential_manager, EventBus())
    with pytest.raises(BrokerNotSupportedException):
        factory.create("ANGEL_ONE")


def test_manager_connect_disconnect(broker_provider: BrokerProvider) -> None:
    """Manager should connect and disconnect broker."""
    broker_provider.manager.connect()
    assert broker_provider.manager.connection_state.value == "CONNECTED"
    broker_provider.manager.disconnect()
    assert broker_provider.manager.connection_state.value == "DISCONNECTED"


def test_stub_brokers_raise(
    broker_config: BrokerConfig,
) -> None:
    """Placeholder brokers should raise not supported."""
    from app.brokers.dhan.broker import DhanBroker
    from app.brokers.zerodha.broker import ZerodhaBroker

    zerodha = ZerodhaBroker(broker_config)
    dhan = DhanBroker(broker_config)
    with pytest.raises(BrokerNotSupportedException):
        zerodha.connect()
    with pytest.raises(BrokerNotSupportedException):
        dhan.connect()
