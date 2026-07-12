"""Repository interfaces package."""

from app.repositories.base_repository import BaseRepository
from app.repositories.repository_factory import RepositoryFactory

__all__ = ["BaseRepository", "RepositoryFactory"]
