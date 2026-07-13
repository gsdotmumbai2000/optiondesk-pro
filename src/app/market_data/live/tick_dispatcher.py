"""Backward-compatible tick dispatcher export."""

from app.market_data.dispatcher.event_dispatcher import EventDispatcher as TickDispatcher

__all__ = ["TickDispatcher"]
