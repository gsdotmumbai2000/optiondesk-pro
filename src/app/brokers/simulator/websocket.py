"""Trivial always-connected websocket shim for the simulator broker.

WebSocketService only ever calls ``set_quote_handler`` on ``broker._websocket``
(see WebSocketService._attach_handler); it never invokes the handler itself.
Simulated ticks are pushed directly into the live EventDispatcher by
ReplayEngine, so the handler registered here is stored but never called.
"""

from collections.abc import Callable
from typing import Any


class SimulatorWebSocket:
    """Stand-in for BreezeWebSocket that never touches a real socket."""

    def __init__(self) -> None:
        """Initialize simulator websocket shim."""
        self._handler: Callable[[Any], None] | None = None
        self.is_connected = False

    def connect(self) -> None:
        """Mark websocket connected."""
        self.is_connected = True

    def disconnect(self) -> None:
        """Mark websocket disconnected."""
        self.is_connected = False

    def set_quote_handler(self, handler: Callable[[Any], None]) -> None:
        """Register application quote handler (unused by the simulator)."""
        self._handler = handler

    def subscribe_quotes(self, subscription: Any) -> None:
        """No-op: simulated ticks are pushed directly, not subscription-driven."""

    def unsubscribe_quotes(self, subscription: Any) -> None:
        """No-op: simulated ticks are pushed directly, not subscription-driven."""

    def subscribe_option_chain(self, request: Any) -> None:
        """No-op: simulated ticks are pushed directly, not subscription-driven."""

    def unsubscribe_option_chain(self, request: Any) -> None:
        """No-op: simulated ticks are pushed directly, not subscription-driven."""
