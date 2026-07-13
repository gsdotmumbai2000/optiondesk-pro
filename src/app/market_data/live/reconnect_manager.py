"""Backward-compatible reconnect manager export."""

from app.market_data.services.reconnect_service import ReconnectService as ReconnectManager

__all__ = ["ReconnectManager"]
