"""Market session model."""

from dataclasses import dataclass

from app.calculation.models.enums import MarketSessionType


@dataclass(frozen=True, slots=True)
class MarketSession:
    """Immutable market session snapshot."""

    exchange: str
    session_type: MarketSessionType
    is_open: bool
    trade_date: str = ""
