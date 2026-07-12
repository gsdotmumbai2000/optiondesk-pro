"""Market data connection state machine."""

from collections.abc import Callable
from enum import Enum
from threading import RLock

from app.brokers.events import (AuthenticationFailedEvent,
                                AuthenticationSucceededEvent,
                                BrokerConnectedEvent, BrokerDisconnectedEvent)
from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger

logger = get_logger(__name__)


class MarketDataConnectionState(str, Enum):
    """Live market data broker connection states."""

    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"
    RECONNECTING = "Reconnecting"
    FAILED = "Failed"


class MarketDataConnectionStateMachine:
    """Gate subscriptions and live processing by broker connection state."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize state machine."""
        self._event_bus = event_bus
        self._lock = RLock()
        self._state = MarketDataConnectionState.DISCONNECTED
        self._on_connected: list[Callable[[], None]] = []
        self._on_disconnected: list[Callable[[], None]] = []

    @property
    def state(self) -> MarketDataConnectionState:
        """Return current connection state."""
        with self._lock:
            return self._state

    @property
    def is_connected(self) -> bool:
        """Return whether live subscriptions are permitted."""
        return self.state == MarketDataConnectionState.CONNECTED

    def can_subscribe(self) -> bool:
        """Return whether broker subscriptions may be sent."""
        return self.is_connected

    def on_connected(self, callback: Callable[[], None]) -> None:
        """Register broker-connected handler."""
        self._on_connected.append(callback)

    def on_disconnected(self, callback: Callable[[], None]) -> None:
        """Register broker-disconnected handler."""
        self._on_disconnected.append(callback)

    def start(self) -> None:
        """Subscribe to broker lifecycle events."""
        if self._event_bus is None:
            return
        self._event_bus.subscribe(BrokerConnectedEvent, self._handle_connected)
        self._event_bus.subscribe(BrokerDisconnectedEvent, self._handle_disconnected)
        self._event_bus.subscribe(
            AuthenticationSucceededEvent, self._handle_connected
        )
        self._event_bus.subscribe(AuthenticationFailedEvent, self._handle_failed)

    def _handle_connected(self, _event: object) -> None:
        with self._lock:
            if self._state == MarketDataConnectionState.CONNECTED:
                return
            self._state = MarketDataConnectionState.CONNECTING
        logger.info("Market data connection: broker ready, activating feed")
        try:
            for callback in self._on_connected:
                callback()
            self._transition(MarketDataConnectionState.CONNECTED)
        except Exception as error:
            logger.warning("Market data activation failed: {error}", error=error)
            self._transition(MarketDataConnectionState.FAILED)

    def _handle_disconnected(self, _event: object) -> None:
        with self._lock:
            if self._state == MarketDataConnectionState.DISCONNECTED:
                return
            self._state = MarketDataConnectionState.RECONNECTING
        logger.info("Market data connection: broker lost, pausing feed")
        for callback in self._on_disconnected:
            try:
                callback()
            except Exception as error:
                logger.warning("Market data pause failed: {error}", error=error)
        self._transition(MarketDataConnectionState.DISCONNECTED)

    def _handle_failed(self, _event: object) -> None:
        self._transition(MarketDataConnectionState.FAILED)

    def _transition(self, new_state: MarketDataConnectionState) -> None:
        with self._lock:
            if self._state == new_state:
                return
            logger.info(
                "Market data state: {old} -> {new}",
                old=self._state.value,
                new=new_state.value,
            )
            self._state = new_state
