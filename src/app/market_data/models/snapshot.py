"""Snapshot and statistics models."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.market_data.models.enums import SnapshotKind
from app.market_data.models.option import OptionChain
from app.market_data.models.quote import Quote


class HistoricalBar(BaseModel):
    """Historical OHLCV bar."""

    symbol: str
    exchange: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int = 0
    open_interest: int | None = None


class MarketSnapshot(BaseModel):
    """Point-in-time market snapshot."""

    snapshot_id: str
    snapshot_kind: SnapshotKind
    captured_at: datetime
    quotes: dict[str, Quote] = Field(default_factory=dict)
    chains: dict[str, OptionChain] = Field(default_factory=dict)


class MarketStatistics(BaseModel):
    """Aggregated market statistics."""

    symbol: str
    exchange: str
    total_volume: int = 0
    total_oi: int = 0
    average_iv: Decimal | None = None
    quote_count: int = 0
    updated_at: datetime | None = None


class MarketStatus(BaseModel):
    """Exchange market status."""

    exchange: str
    is_open: bool
    trade_date: str = ""
    status_code: str = ""
