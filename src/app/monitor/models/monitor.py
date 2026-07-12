"""Position monitor domain models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.monitor.models.enums import MonitoringInterval, MonitorModelVersion, PositionHealth


@dataclass(frozen=True, slots=True)
class MarketDataEventRecord:
    """Normalized market data event reference."""

    event_name: str
    symbol: str
    captured_at: datetime
    payload_key: str = ""


@dataclass(frozen=True, slots=True)
class PositionSnapshot:
    """Point-in-time position observation."""

    position_id: str
    symbol: str
    quantity: int
    unrealized_pnl: Decimal
    health: PositionHealth
    captured_at: datetime


@dataclass(frozen=True, slots=True)
class PositionMonitor:
    """Monitor configuration for a portfolio."""

    monitor_id: str
    portfolio_id: str
    interval: MonitoringInterval
    enabled: bool
    custom_interval_seconds: int = 0
    version: MonitorModelVersion = MonitorModelVersion.V1


@dataclass(frozen=True, slots=True)
class MonitoringSession:
    """Active monitoring session."""

    session_id: str
    monitor_id: str
    portfolio_id: str
    started_at: datetime
    interval: MonitoringInterval
    is_active: bool
    last_evaluated_at: datetime | None = None
