"""Service lifecycle states."""

from enum import Enum


class ServiceLifecycle(str, Enum):
    """Lifecycle states for registered services."""

    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
