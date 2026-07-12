"""Logging manager tests."""

from pathlib import Path

from app.config.models.logging_config import LoggingConfig
from app.logging.logging_manager import LoggingManager


def test_logging_manager_initializes(tmp_path: Path) -> None:
    """Logging manager should initialize file sinks."""
    config = LoggingConfig()
    config.file.enabled = True
    config.console.enabled = False
    config.daily.enabled = False
    config.error.enabled = False
    config.performance.enabled = False
    config.audit.enabled = False
    config.api.enabled = False

    manager = LoggingManager(config, tmp_path)
    manager.initialize()
    manager.get_logger("test").info("logging works")
    manager.shutdown()
    assert (tmp_path / "application.log").exists()


def test_logging_manager_audit_and_api(tmp_path: Path) -> None:
    """Logging manager should support typed log channels."""
    config = LoggingConfig()
    config.console.enabled = False
    config.file.enabled = False
    config.daily.enabled = False
    config.error.enabled = False
    config.performance.enabled = True
    config.audit.enabled = True
    config.api.enabled = True

    manager = LoggingManager(config, tmp_path)
    manager.initialize()
    manager.log_audit("audit event", user="tester")
    manager.log_api("api event", endpoint="/health")
    manager.log_performance("performance event", duration_ms=12)
    manager.shutdown()
