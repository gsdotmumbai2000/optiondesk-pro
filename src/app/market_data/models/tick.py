"""Live tick snapshot models."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.market_data.models.quote import OHLC


class TickSnapshot(BaseModel):
    """Latest tick snapshot for a subscribed instrument."""

    symbol: str
    broker_symbol: str = ""
    exchange: str
    ltp: Decimal | None = None
    ohlc: OHLC = Field(default_factory=OHLC)
    volume: int | None = None
    open_interest: int | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None
    change: Decimal | None = None
    change_percent: Decimal | None = None
    timestamp: datetime | None = None
    product_type: str = ""
    expiry_date: str = ""
    strike_price: str = ""
    option_right: str = ""
