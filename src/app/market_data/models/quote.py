"""Quote and depth domain models."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.market_data.models.enums import InstrumentKind


class Bid(BaseModel):
    """Bid level."""

    price: Decimal
    quantity: int
    orders: int = 0


class Ask(BaseModel):
    """Ask level."""

    price: Decimal
    quantity: int
    orders: int = 0


class OHLC(BaseModel):
    """OHLC price window."""

    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    close: Decimal | None = None


class Depth(BaseModel):
    """Order book depth."""

    bids: list[Bid] = Field(default_factory=list)
    asks: list[Ask] = Field(default_factory=list)


class Trade(BaseModel):
    """Last trade tick."""

    price: Decimal
    quantity: int
    timestamp: datetime


class Quote(BaseModel):
    """Enterprise market quote."""

    symbol: str
    exchange: str
    underlying: str = ""
    instrument_kind: InstrumentKind = InstrumentKind.SPOT
    ltp: Decimal | None = None
    ohlc: OHLC = Field(default_factory=OHLC)
    bid: Decimal | None = None
    ask: Decimal | None = None
    depth: Depth = Field(default_factory=Depth)
    volume: int | None = None
    open_interest: int | None = None
    change: Decimal | None = None
    change_percent: Decimal | None = None
    expiry_date: str = ""
    strike_price: Decimal | None = None
    option_right: str = ""
    timestamp: datetime | None = None
