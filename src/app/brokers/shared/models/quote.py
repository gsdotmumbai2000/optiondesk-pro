"""Quote and market status domain models."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class QuoteDepthLevel(BaseModel):
    """Single depth level."""

    price: Decimal
    quantity: int
    orders: int = 0


class Quote(BaseModel):
    """Normalized live quote."""

    symbol: str
    exchange: str
    ltp: Decimal | None = None
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    close: Decimal | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None
    volume: int | None = None
    open_interest: int | None = None
    change: Decimal | None = None
    change_percent: Decimal | None = None
    timestamp: datetime | None = None
    bid_depth: list[QuoteDepthLevel] = Field(default_factory=list)
    ask_depth: list[QuoteDepthLevel] = Field(default_factory=list)


class MarketStatus(BaseModel):
    """Normalized market status."""

    exchange: str
    is_open: bool
    trade_date: str = ""
    status_code: str = ""
