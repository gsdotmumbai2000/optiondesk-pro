"""Version management."""

from pathlib import Path
from typing import Any

from app.utils.constants import APP_VERSION, BASE_DIR, VERSION_JSON
from app.utils.file_helper import FileHelper


class VersionManager:
    """Manage application and schema version metadata."""

    def __init__(self, version_file: Path | None = None) -> None:
        """Initialize the version manager."""
        self._version_file = version_file or (BASE_DIR / VERSION_JSON)
        self._metadata: dict[str, Any] = {}

    @property
    def application_version(self) -> str:
        """Return the application version."""
        return str(self._metadata.get("application_version", APP_VERSION))

    @property
    def database_schema_version(self) -> int:
        """Return the database schema version."""
        return int(self._metadata.get("database_schema_version", 1))

    @property
    def plugin_api_version(self) -> str:
        """Return the plugin API version."""
        return str(self._metadata.get("plugin_api_version", "1.0.0"))

    @property
    def config_schema_version(self) -> int:
        """Return the configuration schema version."""
        return int(self._metadata.get("config_schema_version", 1))

    def load(self) -> None:
        """Load version metadata from disk."""
        if self._version_file.exists():
            self._metadata = FileHelper.read_json(self._version_file)
        else:
            self._metadata = {
                "application_version": APP_VERSION,
                "database_schema_version": 1,
                "plugin_api_version": "1.0.0",
                "config_schema_version": 1,
            }

    def check_compatibility(self) -> bool:
        """Validate version compatibility."""
        self.load()
        return bool(self.application_version)
