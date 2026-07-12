"""Future and index quote models."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.market_data.models.quote import OHLC


class FutureQuote(BaseModel):
    """Futures contract quote."""

    symbol: str
    exchange: str
    underlying: str
    expiry_date: str
    ltp: Decimal | None = None
    ohlc: OHLC = Field(default_factory=OHLC)
    volume: int | None = None
    open_interest: int | None = None
    timestamp: datetime | None = None


class IndexQuote(BaseModel):
    """Index quote."""

    symbol: str
    exchange: str
    ltp: Decimal | None = None
    ohlc: OHLC = Field(default_factory=OHLC)
    change: Decimal | None = None
    change_percent: Decimal | None = None
    timestamp: datetime | None = None
