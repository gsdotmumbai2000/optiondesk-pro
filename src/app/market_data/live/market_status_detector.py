"""Backward-compatible market status detector export."""

from app.market_data.providers.market_status_detector import (
    MarketStatusDetector,
    MarketStatusSnapshot,
)

__all__ = ["MarketStatusDetector", "MarketStatusSnapshot"]
