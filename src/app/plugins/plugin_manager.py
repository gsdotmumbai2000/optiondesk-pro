"""Plugin manager."""

from pathlib import Path

from app.events.application_events import (PluginLoadedEvent,
                                           PluginUnloadedEvent)
from app.events.event_bus import EventBus
from app.exceptions.plugin_exception import PluginException
from app.kernel.version_manager import VersionManager
from app.logging.logging_manager import get_logger
from app.plugins.plugin_base import PluginBase
from app.plugins.plugin_loader import PluginLoader
from app.plugins.plugin_registry import PluginRegistry

logger = get_logger(__name__)


class PluginManager:
    """Manage plugin discovery, loading, and lifecycle."""

    def __init__(
        self,
        plugin_directory: Path,
        event_bus: EventBus,
        version_manager: VersionManager,
    ) -> None:
        """Initialize the plugin manager."""
        self._plugin_directory = plugin_directory
        self._event_bus = event_bus
        self._version_manager = version_manager
        self._loader = PluginLoader(plugin_directory)
        self._registry = PluginRegistry()

    @property
    def registry(self) -> PluginRegistry:
        """Return the plugin registry."""
        return self._registry

    def discover_and_load(self) -> None:
        """Discover and load all available plugins."""
        manifests = self._loader.discover()
        for manifest_path in manifests:
            try:
                self.load(manifest_path)
            except PluginException as error:
                logger.error("Failed to load plugin: {error}", error=error)

    def load(self, manifest_path: Path) -> PluginBase:
        """Load a plugin from a manifest path."""
        metadata = self._loader.load_metadata(manifest_path)
        self._validate_version(metadata.api_version)
        plugin = self._loader.load_plugin(manifest_path)
        plugin.on_load()
        self._registry.register(plugin)
        self._event_bus.publish(
            PluginLoadedEvent(
                payload={"plugin_key": metadata.plugin_key, "version": metadata.version}
            )
        )
        logger.info("Plugin loaded: {key}", key=metadata.plugin_key)
        return plugin

    def unload(self, plugin_key: str) -> None:
        """Unload a plugin by key."""
        plugin = self._registry.get(plugin_key)
        if plugin is None:
            return
        plugin.on_unload()
        self._registry.unregister(plugin_key)
        self._event_bus.publish(PluginUnloadedEvent(payload={"plugin_key": plugin_key}))
        logger.info("Plugin unloaded: {key}", key=plugin_key)

    def unload_all(self) -> None:
        """Unload all plugins."""
        for metadata in list(self._registry.list_plugins()):
            self.unload(metadata.plugin_key)

    def enable(self, plugin_key: str) -> None:
        """Enable a plugin."""
        plugin = self._registry.get(plugin_key)
        if plugin is None:
            raise PluginException(f"Plugin not found: {plugin_key}")
        plugin.on_enable()

    def disable(self, plugin_key: str) -> None:
        """Disable a plugin."""
        plugin = self._registry.get(plugin_key)
        if plugin is None:
            raise PluginException(f"Plugin not found: {plugin_key}")
        plugin.on_disable()

    def _validate_version(self, plugin_api_version: str) -> None:
        """Validate plugin API compatibility."""
        if plugin_api_version != self._version_manager.plugin_api_version:
            raise PluginException(
                f"Incompatible plugin API version: {plugin_api_version}"
            )
