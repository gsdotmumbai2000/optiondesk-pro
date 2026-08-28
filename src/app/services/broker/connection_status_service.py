"""Broker connection status service."""

from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock

from app.brokers.events import (AuthenticationFailedEvent,
                                AuthenticationSucceededEvent,
                                BrokerConnectedEvent, BrokerDisconnectedEvent,
                                SessionExpiredEvent)
from app.brokers.shared.enums import (BrokerConnectionStatus, BrokerCode,
                                      ConnectionState)
from app.config.models.app_config import BrokerConfig
from app.events.event_bus import EventBus


@dataclass(frozen=True, slots=True)
class BrokerConnectionSnapshot:
    """User-facing broker connection snapshot."""

    broker_name: str
    status: BrokerConnectionStatus
    user_id: str
    environment: str
    account_name: str
    is_session_valid: bool = False


class ConnectionStatusService:
    """Track and expose broker connection status for UI and services."""

    def __init__(
        self,
        config: BrokerConfig,
        event_bus: EventBus | None = None,
        *,
        active_broker_code: Callable[[], str] | None = None,
    ) -> None:
        """Initialize status service.

        ``active_broker_code`` reports which broker is actually connected
        right now; without it, the display falls back to the configured
        live-broker identity, which goes stale once Live/Simulator mode
        switching lets the active broker differ from that config value.
        """
        self._config = config
        self._event_bus = event_bus
        self._active_broker_code = active_broker_code
        self._lock = RLock()
        self._connection_state = ConnectionState.DISCONNECTED
        self._session_valid = False
        if event_bus is not None:
            self._subscribe(event_bus)

    def update_state(
        self,
        state: ConnectionState,
        *,
        session_valid: bool | None = None,
    ) -> BrokerConnectionSnapshot:
        """Update internal state and return snapshot."""
        with self._lock:
            self._connection_state = state
            if session_valid is not None:
                self._session_valid = session_valid
            return self.snapshot()

    def snapshot(self) -> BrokerConnectionSnapshot:
        """Return current connection snapshot."""
        with self._lock:
            return BrokerConnectionSnapshot(
                broker_name=self._broker_display_name(),
                status=self._map_status(),
                user_id=self._config.user_id,
                environment=self._config.environment.value,
                account_name=self._config.account_name,
                is_session_valid=self._session_valid,
            )

    def status_label(self) -> str:
        """Return display label for status bar."""
        snap = self.snapshot()
        user = snap.user_id or snap.account_name
        return (
            f"{snap.broker_name} | {snap.status.value} | "
            f"{user} | {snap.environment.title()}"
        )

    def _broker_display_name(self) -> str:
        code = (
            self._active_broker_code() if self._active_broker_code else self._config.broker_code
        ).upper()
        if code == BrokerCode.BREEZE.value:
            return "ICICI Breeze"
        return code.title()

    def _map_status(self) -> BrokerConnectionStatus:
        state = self._connection_state
        if state == ConnectionState.CONNECTED:
            return BrokerConnectionStatus.CONNECTED
        if state in {ConnectionState.CONNECTING, ConnectionState.AUTHENTICATING}:
            return BrokerConnectionStatus.CONNECTING
        if state == ConnectionState.SESSION_EXPIRED:
            return BrokerConnectionStatus.EXPIRED
        if state == ConnectionState.AUTHENTICATION_FAILED:
            return BrokerConnectionStatus.AUTHENTICATION_FAILED
        if state in {
            ConnectionState.RECONNECTING,
            ConnectionState.RECONNECT_REQUIRED,
            ConnectionState.ERROR,
        }:
            return BrokerConnectionStatus.RECONNECT_REQUIRED
        return BrokerConnectionStatus.DISCONNECTED

    def _subscribe(self, event_bus: EventBus) -> None:
        """Subscribe to broker lifecycle events."""
        event_bus.subscribe(BrokerConnectedEvent, self._on_connected)
        event_bus.subscribe(BrokerDisconnectedEvent, self._on_disconnected)
        event_bus.subscribe(SessionExpiredEvent, self._on_expired)
        event_bus.subscribe(AuthenticationSucceededEvent, self._on_auth_success)
        event_bus.subscribe(AuthenticationFailedEvent, self._on_auth_failed)

    def _on_connected(self, _event: BrokerConnectedEvent) -> None:
        self.update_state(ConnectionState.CONNECTED, session_valid=True)

    def _on_disconnected(self, _event: BrokerDisconnectedEvent) -> None:
        self.update_state(ConnectionState.DISCONNECTED, session_valid=False)

    def _on_expired(self, _event: SessionExpiredEvent) -> None:
        self.update_state(ConnectionState.SESSION_EXPIRED, session_valid=False)

    def _on_auth_success(self, _event: AuthenticationSucceededEvent) -> None:
        self.update_state(ConnectionState.CONNECTED, session_valid=True)

    def _on_auth_failed(self, _event: AuthenticationFailedEvent) -> None:
        self.update_state(ConnectionState.AUTHENTICATION_FAILED, session_valid=False)
