"""Historical data domain models."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.brokers.shared.enums import HistoricalInterval, ProductType


class HistoricalBar(BaseModel):
    """Normalized OHLCV bar."""

    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int = 0
    open_interest: int | None = None


class HistoricalRequest(BaseModel):
    """Historical data request."""

    symbol: str
    exchange: str
    product_type: ProductType
    interval: HistoricalInterval
    from_date: datetime
    to_date: datetime
    expiry_date: str | None = None
    strike_price: Decimal | None = None
    option_right: str | None = None
