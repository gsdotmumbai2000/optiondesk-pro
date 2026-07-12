"""Core application infrastructure."""

from app.core.service_lifecycle import ServiceLifecycle
from app.core.service_registry import ServiceRegistry

__all__ = ["ServiceLifecycle", "ServiceRegistry"]
