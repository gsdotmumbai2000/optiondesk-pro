"""Option market data models."""

from decimal import Decimal

from pydantic import BaseModel, Field


class OptionStrike(BaseModel):
    """Single option strike row."""

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
    call_delta: Decimal | None = None
    put_delta: Decimal | None = None
    is_atm: bool = False


class OptionQuote(BaseModel):
    """Single option contract quote."""

    symbol: str
    exchange: str
    underlying: str
    strike_price: Decimal
    expiry_date: str
    option_right: str
    ltp: Decimal | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None
    volume: int | None = None
    open_interest: int | None = None
    implied_volatility: Decimal | None = None


class OptionChain(BaseModel):
    """Normalized option chain."""

    underlying: str
    exchange: str
    expiry_date: str
    spot_price: Decimal | None = None
    atm_strike: Decimal | None = None
    strikes: list[OptionStrike] = Field(default_factory=list)
