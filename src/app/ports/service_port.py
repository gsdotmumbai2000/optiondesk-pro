"""Base service port."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class IService(Protocol):
    """Marker protocol for application services."""


@runtime_checkable
class IStartable(Protocol):
    """Protocol for startable components."""

    def start(self) -> None:
        """Start the component."""


@runtime_checkable
class IStoppable(Protocol):
    """Protocol for stoppable components."""

    def stop(self) -> None:
        """Stop the component."""
