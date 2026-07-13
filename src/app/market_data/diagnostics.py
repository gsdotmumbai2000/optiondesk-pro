"""Market data pipeline diagnostic configuration and logging helpers."""

from __future__ import annotations

from typing import Any

from loguru import logger as _root_logger

_DEFAULT_ENABLED = True
_enabled: bool | None = None


def configure_market_data_debug(enabled: bool) -> None:
    """Apply diagnostics flag from application configuration."""
    global _enabled
    _enabled = enabled


def market_data_debug_enabled() -> bool:
    """Return whether market data diagnostic logging is active."""
    if _enabled is not None:
        return _enabled
    return _DEFAULT_ENABLED


def _level_enabled(level: str) -> bool:
    """Return whether the active loguru sink level permits the message."""
    try:
        return _root_logger.level(level).no >= _root_logger._core.min_level
    except Exception:
        return True


def log_market_data_diagnostic(
    module_logger: Any,
    prefix: str,
    message: str,
    *,
    level: str = "DEBUG",
    **fields: Any,
) -> None:
    """Emit a gated structured diagnostic log."""
    if not market_data_debug_enabled():
        return
    if not _level_enabled(level):
        return
    formatted = f"[{prefix}] {message}"
    level_name = level.upper()
    if level_name == "INFO":
        module_logger.info(formatted, **fields)
    else:
        module_logger.debug(formatted, **fields)


def log_tick_diagnostic(
    module_logger: Any,
    prefix: str,
    message: str,
    tick: Any,
    *,
    level: str = "DEBUG",
    **extra: Any,
) -> None:
    """Log concise tick fields from a TickSnapshot or tick dict."""
    if not market_data_debug_enabled():
        return
    if not _level_enabled(level):
        return
    fields = _tick_fields(tick)
    fields.update(extra)
    log_market_data_diagnostic(
        module_logger,
        prefix,
        message,
        level=level,
        **fields,
    )


def _tick_fields(tick: Any) -> dict[str, Any]:
    if isinstance(tick, dict):
        return {
            "symbol": tick.get("symbol"),
            "exchange": tick.get("exchange"),
            "ltp": tick.get("ltp"),
            "bid": tick.get("bid"),
            "ask": tick.get("ask"),
            "volume": tick.get("volume"),
            "timestamp": tick.get("timestamp"),
        }
    return {
        "symbol": getattr(tick, "symbol", None),
        "exchange": getattr(tick, "exchange", None),
        "ltp": getattr(tick, "ltp", None),
        "bid": getattr(tick, "bid", None),
        "ask": getattr(tick, "ask", None),
        "volume": getattr(tick, "volume", None),
        "timestamp": getattr(tick, "timestamp", None),
    }
