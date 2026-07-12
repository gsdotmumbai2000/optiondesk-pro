"""Service registry implementation."""

from collections.abc import Callable
from enum import Enum
from threading import RLock
from typing import Any, TypeVar, cast

from app.core.service_lifecycle import ServiceLifecycle
from app.exceptions.application_exception import ApplicationException
from app.logging.logging_manager import get_logger

T = TypeVar("T")
Factory = Callable[[], Any]
logger = get_logger(__name__)


class ServiceScope(str, Enum):
    """Service instantiation scope."""

    SINGLETON = "singleton"
    TRANSIENT = "transient"


class ServiceRegistry:
    """Central registry for application service lifecycle."""

    def __init__(self) -> None:
        """Initialize the service registry."""
        self._factories: dict[str, Factory] = {}
        self._instances: dict[str, Any] = {}
        self._scopes: dict[str, ServiceScope] = {}
        self._lifecycle: dict[str, ServiceLifecycle] = {}
        self._lock = RLock()

    def register(
        self,
        key: str,
        factory: Factory,
        *,
        scope: ServiceScope = ServiceScope.SINGLETON,
    ) -> None:
        """Register a service factory."""
        with self._lock:
            self._factories[key] = factory
            self._scopes[key] = scope
            self._lifecycle[key] = ServiceLifecycle.REGISTERED
            logger.debug("Service registered: {key}", key=key)

    def resolve(self, key: str) -> Any:
        """Resolve a service by key."""
        with self._lock:
            if key not in self._factories:
                raise ApplicationException(f"Service not registered: {key}")

            scope = self._scopes[key]
            if scope == ServiceScope.SINGLETON:
                if key not in self._instances:
                    self._instances[key] = self._factories[key]()
                    self._lifecycle[key] = ServiceLifecycle.INITIALIZED
                return self._instances[key]

            return self._factories[key]()

    def resolve_typed(self, key: str, service_type: type[T]) -> T:
        """Resolve a service and cast to the expected type."""
        return cast(T, self.resolve(key))

    def initialize_all(self) -> None:
        """Initialize all singleton services."""
        with self._lock:
            for key, scope in self._scopes.items():
                if scope != ServiceScope.SINGLETON:
                    continue
                self.resolve(key)
                self._lifecycle[key] = ServiceLifecycle.INITIALIZED
            logger.info("All singleton services initialized")

    def start_all(self) -> None:
        """Start all initialized services."""
        with self._lock:
            for key, instance in self._instances.items():
                starter = getattr(instance, "start", None)
                if callable(starter):
                    starter()
                self._lifecycle[key] = ServiceLifecycle.RUNNING
            logger.info("All services started")

    def stop_all(self) -> None:
        """Stop all running services."""
        with self._lock:
            for key, instance in list(self._instances.items()):
                self._lifecycle[key] = ServiceLifecycle.STOPPING
                stopper = getattr(instance, "stop", None)
                if callable(stopper):
                    stopper()
                self._lifecycle[key] = ServiceLifecycle.STOPPED
            logger.info("All services stopped")

    def get_lifecycle(self, key: str) -> ServiceLifecycle:
        """Return lifecycle state for a service."""
        return self._lifecycle.get(key, ServiceLifecycle.UNREGISTERED)

    def keys(self) -> list[str]:
        """Return registered service keys."""
        return list(self._factories.keys())
