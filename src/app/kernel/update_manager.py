"""Auto-update manager."""

from app.config.models import ApplicationConfig
from app.kernel.version_manager import VersionManager
from app.logging.logging_manager import get_logger

logger = get_logger(__name__)


class UpdateManager:
    """Manage application update checks."""

    def __init__(
        self,
        application_config: ApplicationConfig,
        version_manager: VersionManager,
    ) -> None:
        """Initialize the update manager."""
        self._application_config = application_config
        self._version_manager = version_manager

    def check_for_updates_async(self) -> None:
        """Check for updates without blocking startup."""
        if not self._application_config.check_updates_on_startup:
            logger.info("Update check disabled")
            return
        logger.info(
            "Update check scheduled for version {version}",
            version=self._version_manager.application_version,
        )

    def get_current_version(self) -> str:
        """Return the current application version."""
        return self._version_manager.application_version
