"""Runtime-switchable broker facade.

Everything built against the broker at startup (market data engine,
subscription/websocket services, portfolio/margin adapters) captures a
broker reference once and holds onto it for the life of the app. A
Live <-> Simulator mode switch must not invalidate those references, so
BrokerManager hands out this proxy instead of a concrete broker: its
identity never changes, only the concrete delegate it forwards to.
"""

from typing import Any

from app.brokers.broker_interface.interface import BrokerInterface


class SwitchableBroker:
    """Stable proxy over a swappable concrete broker delegate."""

    def __init__(self, delegate: BrokerInterface) -> None:
        """Initialize proxy around the initial concrete broker."""
        self._delegate = delegate

    @property
    def delegate(self) -> BrokerInterface:
        """Return the currently active concrete broker."""
        return self._delegate

    def replace_delegate(self, new_delegate: BrokerInterface) -> BrokerInterface:
        """Swap in a new concrete broker, returning the previous one."""
        old = self._delegate
        self._delegate = new_delegate
        return old

    def __getattr__(self, name: str) -> Any:
        """Forward any access not defined on the proxy to the delegate."""
        return getattr(self._delegate, name)
