"""Backward-compatible tick cache export."""

from app.market_data.cache.live_tick_cache import LiveTickCache as TickCache

__all__ = ["TickCache"]
