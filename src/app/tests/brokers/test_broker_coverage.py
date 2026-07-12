"""Additional broker coverage tests."""


import pytest

import app.brokers as brokers_package
from app.brokers.bootstrap import BrokerProvider
from app.brokers.breeze.constants import login_url
from app.brokers.breeze.session_manager import BreezeSessionManager
from app.brokers.breeze.websocket import BreezeWebSocket
from app.brokers.broker_manager.state import BrokerConnectionState
from app.brokers.shared.enums import ConnectionState
from app.brokers.shared.exceptions import (BrokerTimeoutException)
from app.brokers.shared.models import OptionChainRequest
from app.brokers.shared.retry import retry_call
from app.config.models.app_config import BrokerConfig
from app.events.event_bus import EventBus
from app.security.credential_manager import CredentialManager
from app.tests.brokers.conftest import MockBreezeClient


def test_lazy_package_exports() -> None:
    """Broker package should expose lazy exports."""
    assert brokers_package.BrokerInterface is not None
    assert brokers_package.BrokerFactory is not None
    assert brokers_package.BrokerManager is not None
    assert brokers_package.BrokerProvider is not None


def test_login_url_encoding() -> None:
    """Login URL should encode API key."""
    url = login_url("key+test")
    assert "api_key=" in url
    assert "key%2Btest" in url


def test_connection_state_tracker() -> None:
    """Connection state tracker should update fields."""
    state = BrokerConnectionState()
    state.set_state(ConnectionState.CONNECTED)
    state.set_session_valid(True)
    state.set_websocket_connected(True)
    state.set_last_heartbeat("now")
    assert state.state == ConnectionState.CONNECTED
    assert state.session_valid is True
    assert state.websocket_connected is True
    assert state.last_heartbeat == "now"


def test_session_manager_refresh(
    credential_manager: CredentialManager,
    broker_config: BrokerConfig,
) -> None:
    """Session manager should validate refreshed session."""
    client = MockBreezeClient("key")
    from app.brokers.breeze.authentication import BreezeAuthentication

    auth = BreezeAuthentication(client, credential_manager, "Default")
    auth.authenticate()
    session = BreezeSessionManager(auth, broker_config)
    session.mark_authenticated()
    assert session.is_session_valid() is True
    session.refresh_session()
    assert session.is_session_valid() is True


def test_websocket_publish_events() -> None:
    """Websocket should publish quote events."""
    bus = EventBus()
    bus.start()
    ws = BreezeWebSocket(MockBreezeClient("key"), bus)
    ws.connect()
    ws.publish_quote("NIFTY", "NFO", [{"ltp": "100"}])
    ws.subscribe_option_chain(
        OptionChainRequest(
            underlying="NIFTY", exchange="NFO", expiry_date="30-Jan-2026"
        )
    )
    ws.unsubscribe_option_chain(
        OptionChainRequest(
            underlying="NIFTY", exchange="NFO", expiry_date="30-Jan-2026"
        )
    )
    ws.resubscribe_all()
    ws.disconnect()
    bus.stop()


def test_retry_call_success() -> None:
    """Retry helper should return on success."""
    assert retry_call(lambda: 42) == 42


def test_retry_call_failure() -> None:
    """Retry helper should exhaust retries."""
    calls = {"count": 0}

    def failing() -> None:
        calls["count"] += 1
        raise BrokerTimeoutException("timeout")

    with pytest.raises(BrokerTimeoutException):
        retry_call(failing, max_retries=2, backoff_ms=1)
    assert calls["count"] == 3


def test_manager_health_without_broker(broker_config: BrokerConfig) -> None:
    """Manager health should work before connect."""
    from app.brokers.broker_factory.factory import BrokerFactory
    from app.brokers.broker_manager.manager import BrokerManager

    factory = BrokerFactory(
        broker_config,
        CredentialManager(),
        EventBus(),
        client_factory=lambda key: MockBreezeClient(key),
    )
    manager = BrokerManager(factory, broker_config, EventBus())
    health = manager.health()
    assert health.connection_state == ConnectionState.DISCONNECTED


def test_broker_logout(broker_provider: BrokerProvider) -> None:
    """Broker logout should disconnect."""
    broker_provider.manager.connect()
    broker_provider.broker_service.logout()
    assert broker_provider.broker_service.health().is_session_valid is False
