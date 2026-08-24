"""Regression test: simulator broker must actually reach CONNECTED state.

Caught via manual end-to-end testing: SimulatorBroker.connect() flips its
own internal flag, but nothing published BrokerConnectedEvent, so
ConnectionStateMachine (which gates EventDispatcher.enqueue via
can_dispatch) never left DISCONNECTED and every replayed tick was silently
dropped. The fix is application_kernel.py calling
BrokerProvider.manager.connect() for the simulator broker -- this test
pins that BrokerManager.connect() alone is sufficient to unblock dispatch,
independent of any UI login action.
"""

from app.brokers.bootstrap import BrokerProvider
from app.config.models.app_config import BrokerConfig
from app.events.event_bus import EventBus
from app.market_data.websocket.connection_state import ConnectionStateMachine
from app.security.credential_manager import CredentialManager


def test_simulator_broker_manager_connect_unblocks_dispatch() -> None:
    """BrokerManager.connect() for SIMULATOR must flip ConnectionStateMachine to connected."""
    event_bus = EventBus()
    provider = BrokerProvider(
        BrokerConfig(broker_code="SIMULATOR"),
        CredentialManager(),
        event_bus,
    )
    connection = ConnectionStateMachine(event_bus)
    connection.start()
    assert not connection.can_subscribe()

    provider.manager.connect()

    assert connection.can_subscribe()
    provider.stop()


def test_simulator_broker_is_connected_without_credentials() -> None:
    """No real credentials should be required to reach CONNECTED."""
    event_bus = EventBus()
    provider = BrokerProvider(
        BrokerConfig(broker_code="SIMULATOR"),
        CredentialManager(),
        event_bus,
    )

    provider.manager.connect()

    assert provider.broker.is_connected()
    provider.stop()
