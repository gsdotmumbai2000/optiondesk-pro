"""Service registry tests."""

from app.core.service_registry import ServiceRegistry, ServiceScope
from app.exceptions.application_exception import ApplicationException


def test_service_registry_singleton() -> None:
    """Singleton services should return the same instance."""
    registry = ServiceRegistry()
    registry.register("counter", lambda: object(), scope=ServiceScope.SINGLETON)
    first = registry.resolve("counter")
    second = registry.resolve("counter")
    assert first is second


def test_service_registry_transient() -> None:
    """Transient services should return new instances."""
    registry = ServiceRegistry()
    registry.register("factory", lambda: object(), scope=ServiceScope.TRANSIENT)
    first = registry.resolve("factory")
    second = registry.resolve("factory")
    assert first is not second


def test_service_registry_missing_service() -> None:
    """Missing services should raise ApplicationException."""
    registry = ServiceRegistry()
    try:
        registry.resolve("missing")
    except ApplicationException:
        return
    raise AssertionError("Expected ApplicationException")
