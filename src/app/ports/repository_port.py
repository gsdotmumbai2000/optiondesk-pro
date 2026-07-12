"""Base repository port."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class IRepository(Protocol):
    """Marker protocol for repository implementations."""

    def initialize(self) -> None:
        """Initialize repository resources."""

    def close(self) -> None:
        """Close repository resources."""
