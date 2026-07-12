"""Market data subscriber registry."""

from collections.abc import Callable
from threading import RLock
from typing import Any

from app.events.application_events import ApplicationEvent


class SubscriberRegistry:
    """Allow downstream modules to subscribe to market data events."""

    def __init__(self) -> None:
        """Initialize registry."""
        self._handlers: dict[str, list[Callable[[ApplicationEvent], None]]] = {}
        self._lock = RLock()

    def subscribe(self, channel: str, handler: Callable[[ApplicationEvent], None]) -> None:
        """Subscribe to a market data channel."""
        with self._lock:
            self._handlers.setdefault(channel, []).append(handler)

    def unsubscribe(self, channel: str, handler: Callable[[ApplicationEvent], None]) -> None:
        """Unsubscribe from a channel."""
        with self._lock:
            handlers = self._handlers.get(channel, [])
            self._handlers[channel] = [item for item in handlers if item is not handler]

    def notify(self, channel: str, event: ApplicationEvent) -> None:
        """Notify subscribers on a channel."""
        with self._lock:
            handlers = list(self._handlers.get(channel, []))
        for handler in handlers:
            handler(event)

    def channels(self) -> list[str]:
        """Return registered channels."""
        with self._lock:
            return list(self._handlers.keys())
