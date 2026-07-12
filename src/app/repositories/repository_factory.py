"""Repository factory."""

from pathlib import Path

from app.config.models import DatabaseConfig
from app.logging.logging_manager import get_logger
from app.repositories.base_repository import BaseRepository

logger = get_logger(__name__)


class RepositoryFactory:
    """Create and manage repository instances."""

    def __init__(self, database_config: DatabaseConfig) -> None:
        """Initialize the repository factory."""
        self._database_config = database_config
        self._repositories: dict[str, BaseRepository] = {}
        self._initialized = False

    @property
    def data_directory(self) -> Path:
        """Return the configured database data directory."""
        return Path(self._database_config.data_directory)

    def initialize(self) -> None:
        """Initialize repository infrastructure."""
        if self._initialized:
            return
        data_dir = self.data_directory
        data_dir.mkdir(parents=True, exist_ok=True)
        self._register_placeholder_repositories()
        for repository in self._repositories.values():
            repository.initialize()
        self._initialized = True
        logger.info("Repository factory initialized at {path}", path=data_dir)

    def close(self) -> None:
        """Close all repositories."""
        for repository in self._repositories.values():
            repository.close()
        self._initialized = False
        logger.info("Repository factory closed")

    def get(self, name: str) -> BaseRepository:
        """Return a repository by name."""
        if name not in self._repositories:
            raise KeyError(f"Repository not registered: {name}")
        return self._repositories[name]

    def register(self, name: str, repository: BaseRepository) -> None:
        """Register a repository instance."""
        self._repositories[name] = repository

    def _register_placeholder_repositories(self) -> None:
        """Register placeholder repositories for future implementation."""
        placeholders = ("config", "market", "strategy", "backtest", "log")
        for name in placeholders:
            self._repositories[name] = BaseRepository()
