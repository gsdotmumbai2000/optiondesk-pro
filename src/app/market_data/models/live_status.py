"""Live market status models."""

from dataclasses import dataclass
from enum import Enum

__all__ = ["LiveMarketStatus", "MarketStatusSnapshot"]


class LiveMarketStatus(str, Enum):
    """User-facing live market status."""

    PRE_OPEN = "Pre Open"
    OPEN = "Open"
    CLOSED = "Closed"
    HOLIDAY = "Holiday"
    CONNECTION_LOST = "Connection Lost"


@dataclass(frozen=True, slots=True)
class MarketStatusSnapshot:
    """Current market status snapshot."""

    status: LiveMarketStatus
    exchange: str
    trade_date: str
    is_holiday: bool = False
