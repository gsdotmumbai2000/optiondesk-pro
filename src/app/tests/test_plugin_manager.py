"""Plugin manager tests."""

from pathlib import Path

from app.events.event_bus import EventBus
from app.kernel.version_manager import VersionManager
from app.plugins.plugin_base import PluginBase
from app.plugins.plugin_manager import PluginManager


class _SamplePlugin(PluginBase):
    """Sample plugin for tests."""

    def on_load(self) -> None:
        self.loaded = True

    def on_unload(self) -> None:
        self.loaded = False


def test_plugin_manager_load_enable_disable(tmp_path: Path) -> None:
    """Plugin manager should load and control plugin state."""
    plugin_dir = tmp_path / "plugins" / "sample"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.yaml").write_text(
        "\n".join(
            [
                "plugin_key: sample",
                "name: Sample",
                "version: 1.0.0",
                "slot_type: INDICATOR",
                "api_version: 1.0.0",
                "entry_point: plugin_impl.py",
            ]
        ),
        encoding="utf-8",
    )
    (plugin_dir / "plugin_impl.py").write_text(
        "\n".join(
            [
                "from app.plugins.plugin_base import PluginBase",
                "class Plugin(PluginBase):",
                "    def on_load(self): pass",
                "    def on_unload(self): pass",
            ]
        ),
        encoding="utf-8",
    )

    event_bus = EventBus()
    version_manager = VersionManager()
    version_manager.load()
    manager = PluginManager(plugin_dir.parent, event_bus, version_manager)
    plugin = manager.load(plugin_dir / "manifest.yaml")
    assert plugin.metadata.plugin_key == "sample"
    manager.enable("sample")
    manager.disable("sample")
    manager.unload("sample")
    assert manager.registry.get("sample") is None
