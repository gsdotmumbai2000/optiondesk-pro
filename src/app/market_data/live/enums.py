"""Live market data enumerations."""

from enum import Enum


class LiveMarketStatus(str, Enum):
    """User-facing live market status."""

    PRE_OPEN = "Pre Open"
    OPEN = "Open"
    CLOSED = "Closed"
    HOLIDAY = "Holiday"
    CONNECTION_LOST = "Connection Lost"


class LiveConnectionStatus(str, Enum):
    """WebSocket connection status."""

    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"
    RECONNECTING = "Reconnecting"
