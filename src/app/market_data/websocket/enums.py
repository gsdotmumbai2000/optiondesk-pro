"""WebSocket connection enumerations."""

from enum import Enum


class LiveConnectionStatus(str, Enum):
    """WebSocket connection status."""

    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"
    RECONNECTING = "Reconnecting"
