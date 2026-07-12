"""Broker connection state tracker."""

from threading import RLock

from app.brokers.shared.enums import ConnectionState


class BrokerConnectionState:
    """Thread-safe broker connection state."""

    def __init__(self) -> None:
        """Initialize disconnected state."""
        self._lock = RLock()
        self._state = ConnectionState.DISCONNECTED
        self._session_valid = False
        self._websocket_connected = False
        self._last_heartbeat = ""

    @property
    def state(self) -> ConnectionState:
        """Return current connection state."""
        with self._lock:
            return self._state

    @property
    def session_valid(self) -> bool:
        """Return whether session is valid."""
        with self._lock:
            return self._session_valid

    @property
    def websocket_connected(self) -> bool:
        """Return websocket connection flag."""
        with self._lock:
            return self._websocket_connected

    @property
    def last_heartbeat(self) -> str:
        """Return last heartbeat timestamp."""
        with self._lock:
            return self._last_heartbeat

    def set_state(self, state: ConnectionState) -> None:
        """Update connection state."""
        with self._lock:
            self._state = state

    def set_session_valid(self, valid: bool) -> None:
        """Update session validity."""
        with self._lock:
            self._session_valid = valid

    def set_websocket_connected(self, connected: bool) -> None:
        """Update websocket flag."""
        with self._lock:
            self._websocket_connected = connected

    def set_last_heartbeat(self, timestamp: str) -> None:
        """Update heartbeat timestamp."""
        with self._lock:
            self._last_heartbeat = timestamp
