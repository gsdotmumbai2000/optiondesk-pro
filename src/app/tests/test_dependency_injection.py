"""Dependency injection tests."""

from pathlib import Path

from app.config.configuration_manager import ConfigurationManager
from app.infrastructure.container import Container


def test_container_resolves_core_dependencies(tmp_path: Path) -> None:
    """Container should resolve core singletons."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "application.yaml").write_text(
        f"schema_version: 1\ndata_directory: '{tmp_path.as_posix()}'\n",
        encoding="utf-8",
    )

    manager = ConfigurationManager(config_dir)
    manager.load()

    container = Container()
    container.configuration_manager.override(manager)

    event_bus = container.event_bus()
    service_registry = container.service_registry()
    scheduler = container.scheduler_manager()

    assert event_bus is not None
    assert service_registry is not None
    assert scheduler.is_running is False
