"""Broker manager."""

from collections.abc import Callable
from datetime import datetime, timezone
from threading import Event, RLock, Thread
from typing import Any

from app.brokers.broker_factory.factory import BrokerFactory
from app.brokers.broker_interface.interface import BrokerInterface
from app.brokers.broker_manager.state import BrokerConnectionState
from app.brokers.broker_manager.switchable_broker import SwitchableBroker
from app.brokers.events import (AuthenticationFailedEvent, BrokerConnectedEvent,
                                BrokerDisconnectedEvent, SessionExpiredEvent)
from app.brokers.shared.enums import ConnectionState
from app.brokers.shared.exceptions import (BrokerAuthenticationException,
                                           BrokerConnectionException,
                                           BrokerSessionExpiredException)
from app.brokers.shared.models import BrokerHealth
from app.brokers.shared.retry import retry_call
from app.config.models.app_config import BrokerConfig
from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger

logger = get_logger(__name__)


class BrokerManager:
    """Manage broker lifecycle, health, and reconnection."""

    def __init__(
        self,
        factory: BrokerFactory,
        config: BrokerConfig,
        event_bus: EventBus | None = None,
        *,
        health_callback: Callable[[bool], None] | None = None,
        initial_code: str | None = None,
    ) -> None:
        """Initialize broker manager."""
        self._factory = factory
        self._config = config
        self._event_bus = event_bus
        self._health_callback = health_callback
        self._broker: SwitchableBroker | None = None
        self._active_code = (initial_code or config.broker_code).upper()
        self._state = BrokerConnectionState()
        self._lock = RLock()
        self._stop_event = Event()
        self._heartbeat_thread: Thread | None = None

    @property
    def broker(self) -> BrokerInterface:
        """Return the active broker instance (a stable proxy; see SwitchableBroker)."""
        if self._broker is None:
            self._broker = SwitchableBroker(self._factory.create(self._active_code))
        return self._broker

    def switch_to(self, new_code: str) -> BrokerHealth:
        """Hot-swap the active broker to `new_code` in place, reconnecting.

        Existing references to `self.broker` (held by the market data
        engine, subscription/websocket services, etc.) stay valid -- only
        the proxy's internal delegate changes.
        """
        new_code = new_code.upper()
        with self._lock:
            if self._broker is not None and self._active_code == new_code:
                return self.health()
            if self._broker is not None:
                self.disconnect()
            new_delegate = self._factory.create(new_code)
            if self._broker is None:
                self._broker = SwitchableBroker(new_delegate)
            else:
                self._broker.replace_delegate(new_delegate)
            self._active_code = new_code
        self.connect()
        return self.health()

    @property
    def connection_state(self) -> ConnectionState:
        """Return current connection state."""
        return self._state.state

    def connect(self) -> None:
        """Connect to the configured broker."""
        with self._lock:
            self._state.set_state(ConnectionState.CONNECTING)
            try:
                retry_call(
                    self._connect_once,
                    max_retries=self._config.reconnect_max_retries,
                    backoff_ms=self._config.reconnect_backoff_ms,
                    retry_on=(BrokerConnectionException,),
                )
            except Exception as error:
                self._state.set_state(ConnectionState.AUTHENTICATION_FAILED)
                self._publish(
                    AuthenticationFailedEvent(
                        payload={"broker": self.broker_code, "reason": str(error)}
                    )
                )
                raise BrokerConnectionException(str(error)) from error

    def disconnect(self) -> None:
        """Disconnect from broker and stop heartbeat."""
        with self._lock:
            self._stop_heartbeat()
            if self._broker is not None:
                self._broker.disconnect()
            self._state.set_state(ConnectionState.DISCONNECTED)
            self._state.set_session_valid(False)
            self._state.set_websocket_connected(False)
            self._notify_health(False)
            self._publish(BrokerDisconnectedEvent(payload={"broker": self.broker_code}))

    def reconnect(self) -> None:
        """Reconnect to broker."""
        with self._lock:
            self._state.set_state(ConnectionState.RECONNECTING)
            self.disconnect()
            self.connect()

    def refresh_session(self) -> None:
        """Refresh broker session."""
        try:
            self.broker.refresh_session()
            self._state.set_session_valid(True)
        except BrokerSessionExpiredException as error:
            self._handle_session_expired()
            raise error

    def health(self) -> BrokerHealth:
        """Return broker health snapshot."""
        broker = self._broker
        if broker is None:
            return BrokerHealth(
                broker_code=self._active_code,
                connection_state=self._state.state,
                is_session_valid=False,
                websocket_connected=False,
                last_heartbeat=self._state.last_heartbeat,
                message="Broker not initialized",
            )
        return broker.health()

    def start_heartbeat(self, interval_sec: int = 30) -> None:
        """Start background heartbeat monitoring."""
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return
        self._stop_event.clear()
        self._heartbeat_thread = Thread(
            target=self._heartbeat_loop,
            args=(interval_sec,),
            name="broker-heartbeat",
            daemon=True,
        )
        self._heartbeat_thread.start()

    def stop(self) -> None:
        """Stop manager and disconnect broker."""
        self.disconnect()

    @property
    def broker_code(self) -> str:
        """Return the currently active broker code (may differ from the
        configured live-broker identity while running in simulator mode)."""
        return self._active_code

    def _connect_once(self) -> None:
        """Perform a single connect attempt."""
        self.broker.connect()
        if self._config.auto_login:
            try:
                self.broker.authenticate()
            except BrokerAuthenticationException as error:
                self._state.set_state(ConnectionState.AUTHENTICATION_FAILED)
                self._publish(
                    AuthenticationFailedEvent(
                        payload={
                            "broker": self.broker_code,
                            "reason": str(error),
                        }
                    )
                )
                raise
        self._state.set_state(ConnectionState.CONNECTED)
        self._state.set_session_valid(True)
        self._notify_health(True)
        self._publish(
            BrokerConnectedEvent(payload={"broker": self.broker.broker_code.value})
        )
        self.start_heartbeat()

    def _heartbeat_loop(self, interval_sec: int) -> None:
        """Run periodic heartbeat checks."""
        while not self._stop_event.wait(interval_sec):
            try:
                health = self.broker.health()
                now = datetime.now(timezone.utc).isoformat()
                self._state.set_last_heartbeat(now)
                self._state.set_websocket_connected(health.websocket_connected)
                if not health.is_session_valid:
                    self._handle_session_expired()
            except Exception as error:
                logger.warning("Broker heartbeat failed: {error}", error=error)

    def _handle_session_expired(self) -> None:
        """Handle session expiry."""
        self._state.set_state(ConnectionState.SESSION_EXPIRED)
        self._state.set_session_valid(False)
        self._notify_health(False)
        self._publish(SessionExpiredEvent(payload={"broker": self.broker_code}))
        self._state.set_state(ConnectionState.RECONNECT_REQUIRED)

    def _stop_heartbeat(self) -> None:
        """Stop heartbeat thread."""
        self._stop_event.set()
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=2)

    def _notify_health(self, connected: bool) -> None:
        """Notify external health monitor."""
        if self._health_callback is not None:
            self._health_callback(connected)

    def _publish(self, event: Any) -> None:
        """Publish broker event."""
        if self._event_bus is not None:
            self._event_bus.publish(event)
