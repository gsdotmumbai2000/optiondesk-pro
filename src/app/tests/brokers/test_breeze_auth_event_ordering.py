"""Tests for AuthenticationSucceededEvent lifecycle ordering.

Regression coverage for the bug where AuthenticationSucceededEvent was
published from BreezeAuthenticationService.login() before
BreezeSessionManager.mark_authenticated() and ConnectionState.CONNECTED
were set on the adapter. Subscribers (e.g. MarketViewModel triggering the
option-chain load) could then call broker APIs that immediately failed
with BrokerConnectionException("Breeze session is not valid"), even though
the event nominally meant "broker session usable".

These tests probe the broker's own state *from inside* the
AuthenticationSucceededEvent handler, at the exact instant the event
fires, which is the only way to prove ordering rather than final state.
"""

from typing import Any

import pytest

from app.brokers.bootstrap import BrokerProvider
from app.brokers.events import AuthenticationFailedEvent, AuthenticationSucceededEvent
from app.brokers.shared.exceptions import BrokerConnectionException
from app.brokers.shared.models import OptionChainRequest
from app.config.models.app_config import BrokerConfig
from app.events.event_bus import EventBus
from app.security.credential_manager import CredentialManager
from app.tests.brokers.conftest import MockBreezeClient


class _FailingAuthClient(MockBreezeClient):
    """Client whose generate_session always fails, for retry/failure tests."""

    def generate_session(self, api_secret: str, session_token: str) -> dict[str, Any]:
        return {"Error": "invalid credentials"}


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
    """Same wiring as the shared broker_provider fixture, with the EventBus exposed."""
    provider = BrokerProvider(
        broker_config,
        credential_manager,
        event_bus,
        client_factory=mock_client_factory,
    )
    yield provider
    provider.stop()


class TestAuthenticationSucceededEventOrdering:
    """AuthenticationSucceededEvent must fire only once the session is usable."""

    def test_event_fires_after_session_marked_authenticated_and_connected(
        self, wired_provider: BrokerProvider, event_bus: EventBus
    ) -> None:
        observed: list[dict] = []

        def probe(event: AuthenticationSucceededEvent) -> None:
            observed.append(
                {
                    "is_connected": wired_provider.broker_service.is_connected(),
                    "is_session_valid": wired_provider.broker_service.health().is_session_valid,
                }
            )

        event_bus.subscribe(AuthenticationSucceededEvent, probe)

        wired_provider.manager.connect()

        assert len(observed) == 1, "AuthenticationSucceededEvent should publish exactly once"
        assert observed[0]["is_connected"] is True
        assert observed[0]["is_session_valid"] is True

    def test_get_option_chain_does_not_raise_when_called_at_event_time(
        self, wired_provider: BrokerProvider, event_bus: EventBus
    ) -> None:
        """Direct reproduction of the reported bug: a subscriber reacting to
        AuthenticationSucceededEvent by calling get_option_chain() (as
        MarketViewModel.load_option_chain() does) must not hit
        BrokerConnectionException("Breeze session is not valid")."""
        results: list[tuple[str, object]] = []

        def probe(event: AuthenticationSucceededEvent) -> None:
            try:
                chain = wired_provider.broker_service.get_option_chain(
                    OptionChainRequest(
                        underlying="NIFTY", exchange="NFO", expiry_date="30-Jan-2026"
                    )
                )
                results.append(("ok", chain))
            except BrokerConnectionException as error:
                results.append(("error", error))

        event_bus.subscribe(AuthenticationSucceededEvent, probe)

        wired_provider.manager.connect()

        assert len(results) == 1
        outcome, payload = results[0]
        assert outcome == "ok", f"get_option_chain() raised at event time: {payload}"
        assert payload.rows[0].strike_price is not None


class TestFailedAuthenticationDoesNotPublishSuccess:
    """A failed authentication must never publish AuthenticationSucceededEvent."""

    def test_failed_authentication_publishes_only_failure_event(
        self, credential_manager: CredentialManager, event_bus: EventBus
    ) -> None:
        config = BrokerConfig(
            broker_code="BREEZE",
            account_name="Default",
            websocket_enabled=False,
            auto_login=True,
            reconnect_max_retries=0,
            reconnect_backoff_ms=1,
        )
        provider = BrokerProvider(
            config,
            credential_manager,
            event_bus,
            client_factory=lambda api_key: _FailingAuthClient(api_key),
        )
        success_events: list[AuthenticationSucceededEvent] = []
        failure_events: list[AuthenticationFailedEvent] = []
        event_bus.subscribe(AuthenticationSucceededEvent, success_events.append)
        event_bus.subscribe(AuthenticationFailedEvent, failure_events.append)

        with pytest.raises(BrokerConnectionException):
            provider.manager.connect()

        assert success_events == []
        # Pre-existing behavior: BreezeAuthenticationService, BrokerManager's
        # _connect_once, and BrokerManager.connect()'s outer catch each
        # publish their own AuthenticationFailedEvent (unrelated to this
        # change). What matters here is that success is never published.
        assert len(failure_events) >= 1
        provider.stop()
