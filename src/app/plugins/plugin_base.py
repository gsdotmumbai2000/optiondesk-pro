"""Plugin base class."""

from abc import ABC, abstractmethod

from app.plugins.plugin_metadata import PluginMetadata


class PluginBase(ABC):
    """Base class for all application plugins."""

    def __init__(self, metadata: PluginMetadata) -> None:
        """Initialize the plugin."""
        self._metadata = metadata
        self._enabled = True

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return self._metadata

    @property
    def is_enabled(self) -> bool:
        """Return whether the plugin is enabled."""
        return self._enabled

    @abstractmethod
    def on_load(self) -> None:
        """Called when the plugin is loaded."""

    @abstractmethod
    def on_unload(self) -> None:
        """Called when the plugin is unloaded."""

    def on_enable(self) -> None:
        """Called when the plugin is enabled."""
        self._enabled = True

    def on_disable(self) -> None:
        """Called when the plugin is disabled."""
        self._enabled = False
