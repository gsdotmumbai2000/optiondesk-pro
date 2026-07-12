"""Configuration manager."""

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.config.models import AppConfiguration
from app.exceptions.configuration_exception import ConfigurationException
from app.utils.constants import (APPLICATION_YAML, BASE_DIR, BROKER_YAML,
                                 CONFIG_DIR, DATABASE_YAML, LOGGING_YAML,
                                 PLUGINS_YAML, RISK_YAML, SCHEDULER_YAML,
                                 UI_YAML)
from app.utils.file_helper import FileHelper
from app.utils.json_helper import JsonHelper


class ConfigurationManager:
    """Load, validate, and persist application configuration."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize the configuration manager."""
        self._config_dir = config_dir or CONFIG_DIR
        self._user_config_dir: Path | None = None
        self._configuration = AppConfiguration()

    @property
    def configuration(self) -> AppConfiguration:
        """Return the active configuration."""
        return self._configuration

    @property
    def config_dir(self) -> Path:
        """Return the active configuration directory."""
        if self._user_config_dir is not None:
            return self._user_config_dir
        return self._config_dir

    def set_user_config_dir(self, path: Path) -> None:
        """Set the user-specific configuration directory."""
        self._user_config_dir = path
        FileHelper.ensure_directory(path)

    def load(self) -> AppConfiguration:
        """Load configuration from YAML files."""
        merged = self._load_defaults()
        merged.update(self._load_directory(self._config_dir))
        if self._user_config_dir is not None:
            merged.update(self._load_directory(self._user_config_dir))

        try:
            self._configuration = AppConfiguration.model_validate(merged)
        except ValidationError as error:
            raise ConfigurationException(
                f"Configuration validation failed: {error}"
            ) from error

        self._apply_data_directory()
        return self._configuration

    def save(self) -> None:
        """Persist configuration to the user config directory."""
        target_dir = self._user_config_dir or self._config_dir
        FileHelper.ensure_directory(target_dir)
        payload = self._configuration.model_dump(mode="json")
        self._write_split_config(target_dir, payload)

    def reload(self) -> AppConfiguration:
        """Reload configuration from disk."""
        return self.load()

    def validate(self) -> bool:
        """Validate the active configuration."""
        try:
            AppConfiguration.model_validate(self._configuration.model_dump(mode="json"))
        except ValidationError as error:
            raise ConfigurationException(f"Configuration invalid: {error}") from error
        return True

    def _load_defaults(self) -> dict[str, Any]:
        """Load built-in default configuration."""
        return AppConfiguration().model_dump(mode="json")

    def _load_directory(self, directory: Path) -> dict[str, Any]:
        """Load all known YAML files from a directory."""
        if not directory.exists():
            return {}

        mapping = {
            "application": APPLICATION_YAML,
            "database": DATABASE_YAML,
            "broker": BROKER_YAML,
            "logging": LOGGING_YAML,
            "ui": UI_YAML,
            "risk": RISK_YAML,
            "scheduler": SCHEDULER_YAML,
            "plugins": PLUGINS_YAML,
        }
        merged: dict[str, Any] = {}
        for key, filename in mapping.items():
            path = directory / filename
            if path.exists():
                merged[key] = FileHelper.read_yaml(path)
        return merged

    def _write_split_config(self, directory: Path, payload: dict[str, Any]) -> None:
        """Write configuration sections to individual YAML files."""
        files = {
            APPLICATION_YAML: payload.get("application", {}),
            DATABASE_YAML: payload.get("database", {}),
            BROKER_YAML: payload.get("broker", {}),
            LOGGING_YAML: payload.get("logging", {}),
            UI_YAML: payload.get("ui", {}),
            RISK_YAML: payload.get("risk", {}),
            SCHEDULER_YAML: payload.get("scheduler", {}),
            PLUGINS_YAML: payload.get("plugins", {}),
        }
        for filename, data in files.items():
            FileHelper.write_yaml(directory / filename, data)

    def _apply_data_directory(self) -> None:
        """Apply resolved data directory paths."""
        app_data = self._configuration.application.data_directory
        if not app_data:
            app_data = str(self._resolve_default_data_dir())
            self._configuration.application.data_directory = app_data

        data_path = Path(app_data)
        FileHelper.ensure_directory(data_path)

        db_config = self._configuration.database
        if not db_config.data_directory:
            db_config.data_directory = str(data_path)

    def _resolve_default_data_dir(self) -> Path:
        """Resolve the default per-user data directory."""
        appdata = Path.home() / "AppData" / "Local" / "OptionDeskPro"
        if BASE_DIR.name == "optiondesk-pro":
            return appdata
        return BASE_DIR / "data"

    def export_json(self, path: Path) -> None:
        """Export the active configuration to JSON."""
        payload = JsonHelper.model_to_dict(self._configuration)
        FileHelper.write_json(path, payload)
