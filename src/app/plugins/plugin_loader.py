"""Plugin loader."""

import importlib.util
from pathlib import Path

from app.exceptions.plugin_exception import PluginException
from app.logging.logging_manager import get_logger
from app.plugins.plugin_base import PluginBase
from app.plugins.plugin_metadata import PluginMetadata
from app.utils.file_helper import FileHelper

logger = get_logger(__name__)


class PluginLoader:
    """Discover and load plugins from the filesystem."""

    def __init__(self, plugin_directory: Path) -> None:
        """Initialize the plugin loader."""
        self._plugin_directory = plugin_directory

    def discover(self) -> list[Path]:
        """Discover plugin manifest files."""
        if not self._plugin_directory.exists():
            return []
        return sorted(self._plugin_directory.glob("*/manifest.yaml"))

    def load_metadata(self, manifest_path: Path) -> PluginMetadata:
        """Load plugin metadata from a manifest file."""
        data = FileHelper.read_yaml(manifest_path)
        try:
            return PluginMetadata.model_validate(data)
        except Exception as error:
            raise PluginException(
                f"Invalid plugin manifest: {manifest_path}"
            ) from error

    def load_plugin(self, manifest_path: Path) -> PluginBase:
        """Load a plugin instance from a manifest path."""
        metadata = self.load_metadata(manifest_path)
        plugin_dir = manifest_path.parent
        entry_path = plugin_dir / metadata.entry_point
        if not entry_path.exists():
            raise PluginException(f"Plugin entry point not found: {entry_path}")

        module_name = f"optiondesk_plugin_{metadata.plugin_key.replace('-', '_')}"
        spec = importlib.util.spec_from_file_location(module_name, entry_path)
        if spec is None or spec.loader is None:
            raise PluginException(f"Unable to load plugin module: {entry_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plugin_class = getattr(module, "Plugin", None)
        if plugin_class is None:
            raise PluginException(f"Plugin class not found in: {entry_path}")

        plugin = plugin_class(metadata)
        if not isinstance(plugin, PluginBase):
            raise PluginException(
                f"Plugin must extend PluginBase: {metadata.plugin_key}"
            )

        logger.info("Plugin module loaded: {key}", key=metadata.plugin_key)
        return plugin
