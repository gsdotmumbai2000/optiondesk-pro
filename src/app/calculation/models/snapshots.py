"""Calculation quote snapshot models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class SpotQuoteSnapshot:
    """Immutable spot/index quote snapshot."""

    symbol: str
    exchange: str
    ltp: Decimal
    timestamp: datetime | None = None


@dataclass(frozen=True, slots=True)
class FutureQuoteSnapshot:
    """Immutable futures quote snapshot."""

    symbol: str
    exchange: str
    underlying: str
    expiry_date: str
    ltp: Decimal
    open_interest: int | None = None
    volume: int | None = None
    timestamp: datetime | None = None


@dataclass(frozen=True, slots=True)
class OptionStrikeSnapshot:
    """Immutable option strike snapshot."""

    strike_price: Decimal
    call_ltp: Decimal | None = None
    put_ltp: Decimal | None = None
    call_oi: int | None = None
    put_oi: int | None = None
    call_iv: Decimal | None = None
    put_iv: Decimal | None = None
    is_atm: bool = False


@dataclass(frozen=True, slots=True)
class OptionChainSnapshot:
    """Immutable option chain snapshot."""

    underlying: str
    exchange: str
    expiry_date: str
    spot_price: Decimal | None
    atm_strike: Decimal | None
    strikes: tuple[OptionStrikeSnapshot, ...] = ()
