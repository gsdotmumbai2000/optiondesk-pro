"""Configuration manager tests."""

from pathlib import Path

import pytest

from app.config.configuration_manager import ConfigurationManager
from app.exceptions.configuration_exception import ConfigurationException


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """Create a temporary configuration directory."""
    config_path = tmp_path / "config"
    config_path.mkdir()
    (config_path / "application.yaml").write_text(
        "schema_version: 1\nenvironment: test\n",
        encoding="utf-8",
    )
    return config_path


def test_configuration_load_and_validate(config_dir: Path) -> None:
    """Configuration should load and validate."""
    manager = ConfigurationManager(config_dir)
    configuration = manager.load()
    assert configuration.application.environment == "test"
    assert manager.validate() is True


def test_configuration_save_round_trip(config_dir: Path, tmp_path: Path) -> None:
    """Configuration should persist to user config directory."""
    manager = ConfigurationManager(config_dir)
    manager.load()
    manager.set_user_config_dir(tmp_path / "user_config")
    manager.configuration.application.environment = "saved"
    manager.save()
    reloaded = ConfigurationManager(config_dir)
    reloaded.set_user_config_dir(tmp_path / "user_config")
    configuration = reloaded.load()
    assert configuration.application.environment == "saved"


def test_configuration_reload(config_dir: Path) -> None:
    """Configuration reload should refresh values."""
    manager = ConfigurationManager(config_dir)
    manager.load()
    reloaded = manager.reload()
    assert reloaded.application.schema_version == 1


def test_configuration_export_json(config_dir: Path, tmp_path: Path) -> None:
    """Configuration export should write JSON."""
    manager = ConfigurationManager(config_dir)
    manager.load()
    export_path = tmp_path / "config.json"
    manager.export_json(export_path)
    assert export_path.exists()


def test_configuration_validation_failure(config_dir: Path) -> None:
    """Invalid configuration should raise ConfigurationException."""
    (config_dir / "application.yaml").write_text(
        "schema_version: not-an-integer\n",
        encoding="utf-8",
    )
    manager = ConfigurationManager(config_dir)
    with pytest.raises(ConfigurationException):
        manager.load()
