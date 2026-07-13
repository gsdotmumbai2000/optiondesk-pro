"""Live option chain models."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.live.models.enums import ChainSide


class LiveOptionLeg(BaseModel):
    """Single call or put quote in the live chain."""

    symbol: str
    exchange: str
    underlying: str
    strike_price: Decimal
    expiry_date: str
    side: ChainSide
    ltp: Decimal | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None
    volume: int | None = None
    open_interest: int | None = None
    implied_volatility: Decimal | None = None
    delta: Decimal | None = None
    gamma: Decimal | None = None
    theta: Decimal | None = None
    vega: Decimal | None = None
    timestamp: datetime | None = None


class LiveOptionStrike(BaseModel):
    """Aggregated strike row with call and put legs."""

    strike_price: Decimal
    call: LiveOptionLeg | None = None
    put: LiveOptionLeg | None = None
    is_atm: bool = False


class LiveOptionChain(BaseModel):
    """Thread-safe live option chain snapshot."""

    underlying: str
    exchange: str
    expiry_date: str
    spot_price: Decimal | None = None
    future_price: Decimal | None = None
    atm_strike: Decimal | None = None
    strikes: dict[str, LiveOptionStrike] = Field(default_factory=dict)
    updated_at: datetime | None = None

    def strike_list(self) -> tuple[LiveOptionStrike, ...]:
        """Return strikes sorted by price."""
        ordered = sorted(self.strikes.values(), key=lambda row: row.strike_price)
        return tuple(ordered)
