"""Backward-compatible websocket manager export."""

from app.market_data.websocket.websocket_service import WebSocketService as WebSocketManager

__all__ = ["WebSocketManager"]
