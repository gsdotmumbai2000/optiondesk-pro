"""Historical data models for backtesting."""

from dataclasses import dataclass
from datetime import datetime

from app.market_data.models.snapshot import HistoricalBar


@dataclass(frozen=True, slots=True)
class HistoricalMarketData:
    """Immutable historical market data bundle."""

    underlying: str
    exchange: str
    bars: tuple[HistoricalBar, ...]


@dataclass(frozen=True, slots=True)
class HistoricalOptionChainSnapshot:
    """Historical option chain at a point in time."""

    timestamp: datetime
    chain_id: str
    underlying: str
    strikes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class HistoricalOptionChainData:
    """Immutable historical option chain series."""

    underlying: str
    snapshots: tuple[HistoricalOptionChainSnapshot, ...]
