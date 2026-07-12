"""Option chain domain models."""

from decimal import Decimal

from pydantic import BaseModel, Field

from app.brokers.shared.enums import OptionRight


class OptionChainLeg(BaseModel):
    """Single option chain strike row."""

    strike_price: Decimal
    expiry_date: str
    call_symbol: str = ""
    put_symbol: str = ""
    call_ltp: Decimal | None = None
    put_ltp: Decimal | None = None
    call_oi: int | None = None
    put_oi: int | None = None
    call_volume: int | None = None
    put_volume: int | None = None
    call_iv: Decimal | None = None
    put_iv: Decimal | None = None
    call_bid: Decimal | None = None
    call_ask: Decimal | None = None
    put_bid: Decimal | None = None
    put_ask: Decimal | None = None
    call_delta: Decimal | None = None
    put_delta: Decimal | None = None
    is_atm: bool = False


class OptionChain(BaseModel):
    """Normalized option chain."""

    underlying: str
    exchange: str
    expiry_date: str
    spot_price: Decimal | None = None
    atm_strike: Decimal | None = None
    calls: list[OptionChainLeg] = Field(default_factory=list)
    puts: list[OptionChainLeg] = Field(default_factory=list)
    rows: list[OptionChainLeg] = Field(default_factory=list)


class OptionChainRequest(BaseModel):
    """Option chain request parameters."""

    underlying: str
    exchange: str
    expiry_date: str
    right: OptionRight | None = None
    strike_price: Decimal | None = None
