"""Mock websocket for live market data tests."""

from collections.abc import Callable
from typing import Any


class MockWebSocket:
    """Simulate broker websocket callbacks."""

    def __init__(self) -> None:
        """Initialize mock websocket."""
        self._handler: Callable[[Any], None] | None = None
        self.connected = False
        self.subscriptions: list[dict[str, str]] = []

    def connect(self) -> None:
        """Mark websocket connected."""
        self.connected = True

    def disconnect(self) -> None:
        """Mark websocket disconnected."""
        self.connected = False

    def set_quote_handler(self, handler: Callable[[Any], None]) -> None:
        """Attach tick handler."""
        self._handler = handler

    def subscribe(self, symbol: str, exchange: str = "NSE") -> None:
        """Track subscription."""
        self.subscriptions.append({"symbol": symbol, "exchange": exchange})

    def emit_tick(self, payload: dict[str, Any]) -> None:
        """Emit synthetic tick to handler."""
        if self._handler is not None:
            self._handler(payload)
