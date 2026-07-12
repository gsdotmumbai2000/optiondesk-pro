"""Plugin registry."""

from app.plugins.plugin_base import PluginBase
from app.plugins.plugin_metadata import PluginMetadata


class PluginRegistry:
    """In-memory registry of loaded plugins."""

    def __init__(self) -> None:
        """Initialize the plugin registry."""
        self._plugins: dict[str, PluginBase] = {}
        self._metadata: dict[str, PluginMetadata] = {}

    def register(self, plugin: PluginBase) -> None:
        """Register a loaded plugin."""
        key = plugin.metadata.plugin_key
        self._plugins[key] = plugin
        self._metadata[key] = plugin.metadata

    def unregister(self, plugin_key: str) -> None:
        """Unregister a plugin."""
        self._plugins.pop(plugin_key, None)
        self._metadata.pop(plugin_key, None)

    def get(self, plugin_key: str) -> PluginBase | None:
        """Return a plugin by key."""
        return self._plugins.get(plugin_key)

    def get_metadata(self, plugin_key: str) -> PluginMetadata | None:
        """Return plugin metadata by key."""
        return self._metadata.get(plugin_key)

    def list_plugins(self) -> list[PluginMetadata]:
        """Return metadata for all registered plugins."""
        return list(self._metadata.values())

    def list_enabled(self) -> list[PluginBase]:
        """Return all enabled plugins."""
        return [plugin for plugin in self._plugins.values() if plugin.is_enabled]
