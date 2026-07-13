"""Enterprise live market tick model."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.market_data.models.enums import InstrumentKind
from app.market_data.models.quote import OHLC


class GreeksSnapshot(BaseModel):
    """Optional greeks attached to a live tick."""

    delta: Decimal | None = None
    gamma: Decimal | None = None
    theta: Decimal | None = None
    vega: Decimal | None = None
    rho: Decimal | None = None


class MarketTick(BaseModel):
    """Thread-safe live tick payload for cache and events."""

    symbol: str
    exchange: str
    instrument_kind: InstrumentKind = InstrumentKind.SPOT
    ltp: Decimal | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None
    ohlc: OHLC = Field(default_factory=OHLC)
    volume: int | None = None
    open_interest: int | None = None
    implied_volatility: Decimal | None = None
    greeks: GreeksSnapshot = Field(default_factory=GreeksSnapshot)
    change: Decimal | None = None
    change_percent: Decimal | None = None
    timestamp: datetime | None = None
    expiry_date: str = ""
    strike_price: str = ""
    option_right: str = ""
    product_type: str = ""
