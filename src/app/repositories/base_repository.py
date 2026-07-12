"""Base repository implementation."""

from app.ports.repository_port import IRepository


class BaseRepository(IRepository):
    """Base class for repository adapters."""

    def initialize(self) -> None:
        """Initialize repository resources."""

    def close(self) -> None:
        """Close repository resources."""
