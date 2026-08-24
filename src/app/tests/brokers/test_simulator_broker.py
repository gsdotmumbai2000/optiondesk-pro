"""Simulator broker tests."""

import pytest

from app.brokers.broker_factory.factory import BrokerFactory
from app.brokers.shared.enums import BrokerCode, ConnectionState
from app.brokers.shared.exceptions import BrokerNotSupportedException
from app.brokers.simulator.broker import SimulatorBroker
from app.config.models.app_config import BrokerConfig
from app.events.event_bus import EventBus
from app.security.credential_manager import CredentialManager


@pytest.fixture
def simulator_broker() -> SimulatorBroker:
    """Return a fresh simulator broker."""
    return SimulatorBroker(BrokerConfig(broker_code="SIMULATOR"))


def test_factory_creates_simulator(
    credential_manager: CredentialManager,
) -> None:
    """Factory should create the simulator broker for broker_code=SIMULATOR."""
    config = BrokerConfig(broker_code="SIMULATOR")
    factory = BrokerFactory(config, credential_manager, EventBus())
    broker = factory.create()
    assert isinstance(broker, SimulatorBroker)
    assert broker.broker_code == BrokerCode.SIMULATOR


def test_connect_without_credentials(simulator_broker: SimulatorBroker) -> None:
    """Simulator should connect without any real network/credentials."""
    assert not simulator_broker.is_connected()
    simulator_broker.connect()
    assert simulator_broker.is_connected()
    assert simulator_broker.connection_state == ConnectionState.CONNECTED
    assert simulator_broker.health().websocket_connected


def test_disconnect(simulator_broker: SimulatorBroker) -> None:
    """Simulator should disconnect cleanly."""
    simulator_broker.connect()
    simulator_broker.disconnect()
    assert not simulator_broker.is_connected()
    assert simulator_broker.connection_state == ConnectionState.DISCONNECTED


def test_account_methods_return_empty_results(simulator_broker: SimulatorBroker) -> None:
    """Account/portfolio methods should return neutral results, not raise."""
    assert simulator_broker.get_funds().available_cash == 0
    assert simulator_broker.get_holdings() == []
    assert simulator_broker.get_positions() == []
    assert simulator_broker.get_orders("NFO") == []
    assert simulator_broker.calculate_margin([], "NFO") is None


def test_trading_actions_unsupported(simulator_broker: SimulatorBroker) -> None:
    """Order placement should raise a clear not-supported error."""
    with pytest.raises(BrokerNotSupportedException):
        simulator_broker.place_order(object())  # type: ignore[arg-type]
