"""Regression coverage for the websocket-connect-before-subscribe ordering bug.

BreezeBrokerAdapter.authenticate() used to publish AuthenticationSucceededEvent
before calling self._websocket.connect(). AuthenticationSucceededEvent is
delivered synchronously and its subscribers include the default-subscription
activation path (SubscriptionService.activate_pending(), via
LiveMarketDataProvider._activate_live_feed()), which calls the broker's
subscribe_quotes() immediately. The installed Breeze SDK's subscribe_feeds()
silently no-ops (returns None, not an error) when its own websocket handler
has not connected yet, so subscriptions issued in that window never actually
reach Breeze even though the application logs them as successful.

This test proves the fix by asserting BreezeWebSocket.connect() is invoked
before AuthenticationSucceededEvent is published, using the same event-bus
probe pattern as test_breeze_auth_event_ordering.py.
"""

from unittest.mock import patch

import pytest

from app.brokers.bootstrap import BrokerProvider
from app.brokers.breeze.websocket import BreezeWebSocket
from app.brokers.events import AuthenticationSucceededEvent
from app.config.models.app_config import BrokerConfig
from app.events.event_bus import EventBus
from app.security.credential_manager import CredentialManager


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def wired_provider(
    broker_config: BrokerConfig,
    credential_manager: CredentialManager,
    mock_client_factory,
    event_bus: EventBus,
) -> BrokerProvider:
    provider = BrokerProvider(
        broker_config,
        credential_manager,
        event_bus,
        client_factory=mock_client_factory,
    )
    yield provider
    provider.stop()


class TestWebsocketConnectOrdering:
    """BreezeWebSocket.connect() must run before AuthenticationSucceededEvent."""

    def test_websocket_connect_called_before_authentication_succeeded_event(
        self, wired_provider: BrokerProvider, event_bus: EventBus
    ) -> None:
        sequence: list[str] = []
        original_connect = BreezeWebSocket.connect

        def recording_connect(self: BreezeWebSocket) -> None:
            sequence.append("websocket_connect")
            return original_connect(self)

        def probe(_event: AuthenticationSucceededEvent) -> None:
            sequence.append("authentication_succeeded_event")

        event_bus.subscribe(AuthenticationSucceededEvent, probe)

        with patch.object(BreezeWebSocket, "connect", recording_connect):
            wired_provider.manager.connect()

        assert "websocket_connect" in sequence
        assert "authentication_succeeded_event" in sequence
        assert sequence.index("websocket_connect") < sequence.index(
            "authentication_succeeded_event"
        ), (
            "BreezeWebSocket.connect() must be called before "
            "AuthenticationSucceededEvent is published, otherwise default "
            "subscriptions activated by that event are silently dropped by "
            "the Breeze SDK. Observed order: " + repr(sequence)
        )
