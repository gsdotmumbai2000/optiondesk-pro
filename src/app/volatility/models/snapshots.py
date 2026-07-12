"""Volatility snapshot models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class VolatilityMarketSnapshot:
    """Market snapshot for volatility analytics."""

    snapshot_id: str
    underlying: str
    exchange: str
    spot_price: Decimal
    captured_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class HistoricalDataSnapshot:
    """Historical price data for realized volatility."""

    underlying: str
    closes: tuple[Decimal, ...] = ()
    returns: tuple[Decimal, ...] = ()
