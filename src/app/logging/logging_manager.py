"""Loguru-based logging manager."""

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from loguru import logger

from app.config.models.logging_config import (
    ApiLogConfig,
    AuditLogConfig,
    DailyLogConfig,
    ErrorLogConfig,
    LoggingConfig,
    PerformanceLogConfig,
)
from app.utils.file_helper import FileHelper


class LoggingManager:
    """Configure and manage application logging sinks."""

    def __init__(self, config: LoggingConfig, log_directory: Path) -> None:
        """Initialize the logging manager."""
        self._config = config
        self._log_directory = log_directory
        self._configured = False

    def initialize(self) -> None:
        """Configure Loguru sinks."""
        if self._configured:
            return

        logger.remove()
        FileHelper.ensure_directory(self._log_directory)
        self._configure_console()
        self._configure_file_sinks()
        self._configured = True
        logger.info("Logging initialized")

    def shutdown(self) -> None:
        """Flush and release logging resources."""
        logger.info("Logging shutdown")
        logger.complete()

    def get_logger(self, name: str) -> Any:
        """Return a named logger instance."""
        return logger.bind(module=name)

    def log_audit(self, message: str, **context: object) -> None:
        """Write an audit log entry."""
        logger.bind(log_type="audit", **context).info(message)

    def log_api(self, message: str, **context: object) -> None:
        """Write an API log entry."""
        logger.bind(log_type="api", **context).debug(message)

    def log_performance(self, message: str, **context: object) -> None:
        """Write a performance log entry."""
        logger.bind(log_type="performance", **context).info(message)

    def log_crash_report(
        self,
        *,
        exception_type: str,
        exception_message: str,
        stack_trace: str,
    ) -> None:
        """Write a crash report entry."""
        crash_path = self._log_directory / "crash_reports.log"
        logger.bind(
            log_type="crash",
            exception_type=exception_type,
            exception_message=exception_message,
        ).critical(stack_trace)
        FileHelper.write_text(crash_path, stack_trace, encoding="utf-8")

    def _configure_console(self) -> None:
        """Configure console logging."""
        console = self._config.console
        if not console.enabled:
            return
        logger.add(
            sys.stderr,
            level=console.level,
            colorize=console.colorize,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{extra[module]}</cyan> - "
                "<level>{message}</level>"
            ),
            filter=lambda record: record["extra"].setdefault("module", "app") or True,
        )

    def _configure_file_sinks(self) -> None:
        """Configure file-based logging sinks."""
        file_cfg = self._config.file
        if file_cfg.enabled:
            logger.add(
                str(self._resolve_log_path(file_cfg.path)),
                level=file_cfg.level,
                rotation=file_cfg.rotation,
                retention=file_cfg.retention,
                compression=file_cfg.compression,
                encoding="utf-8",
            )

        self._add_sink(self._config.daily, "daily", include_filter=False)
        self._add_sink(self._config.error, "error")
        self._add_sink(self._config.performance, "performance")
        self._add_sink(self._config.audit, "audit")
        self._add_sink(self._config.api, "api")

    def _add_sink(
        self,
        sink_config: DailyLogConfig
        | ErrorLogConfig
        | PerformanceLogConfig
        | AuditLogConfig
        | ApiLogConfig,
        sink_name: str,
        *,
        include_filter: bool = True,
    ) -> None:
        """Add a typed file sink configuration."""
        if not sink_config.enabled:
            return

        kwargs: dict[str, Any] = {
            "level": sink_config.level,
            "encoding": "utf-8",
        }
        rotation = getattr(sink_config, "rotation", None)
        retention = getattr(sink_config, "retention", None)
        compression = getattr(sink_config, "compression", None)
        if rotation:
            kwargs["rotation"] = rotation
        if retention:
            kwargs["retention"] = retention
        if compression:
            kwargs["compression"] = compression
        if include_filter:
            log_filter: Callable[..., bool] = (
                lambda record, name=sink_name: record["extra"].get("log_type") == name
            )
            kwargs["filter"] = log_filter
        logger.add(str(self._resolve_log_path(sink_config.path)), **kwargs)

    def _resolve_log_path(self, configured_path: str) -> Path:
        """Resolve a log file path relative to the log directory."""
        if "{" in configured_path:
            return self._log_directory / "daily"
        path = Path(configured_path)
        if path.is_absolute():
            return path
        return self._log_directory / path.name


def get_logger(name: str) -> Any:
    """Return a module-bound logger."""
    return logger.bind(module=name)
