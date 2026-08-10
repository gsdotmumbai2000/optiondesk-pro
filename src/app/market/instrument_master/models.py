"""Instrument master domain models."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.market.enums import ExchangeCode, InstrumentType


class InstrumentSpecification(BaseModel):
    """Trading specification for an instrument."""

    tick_size: Decimal
    lot_size: int
    freeze_quantity: int
    strike_interval: Decimal
    price_precision: int = 2
    quantity_precision: int = 0
    contract_multiplier: int = 1


class ExpiryRulesRef(BaseModel):
    """Reference to expiry rule configuration."""

    weekly_expiry_day: str | None = None
    monthly_expiry_rule: str = "LAST_WEEKDAY"
    monthly_expiry_day: str | None = None
    supports_weekly: bool = True
    supports_monthly: bool = True
    supports_quarterly: bool = False


class TradingHoursRef(BaseModel):
    """Reference to trading session configuration."""

    session_profile: str = "NSEFO_REGULAR"
    pre_open_start: str = "09:00:00"
    pre_open_end: str = "09:08:00"
    market_open: str = "09:15:00"
    market_close: str = "15:30:00"
    post_close_end: str = "16:00:00"


class Instrument(BaseModel):
    """Canonical tradable instrument record."""

    instrument_id: str
    trading_symbol: str
    display_name: str
    underlying: str
    exchange: ExchangeCode
    segment: str
    instrument_type: InstrumentType
    currency: str = "INR"
    specification: InstrumentSpecification
    trading_hours: TradingHoursRef = Field(default_factory=TradingHoursRef)
    expiry_rules: ExpiryRulesRef = Field(default_factory=ExpiryRulesRef)
    is_active: bool = True
    expiry_date: date | None = None
    strike_price: Decimal | None = None
    option_right: str | None = None
    broker_symbols: dict[str, str] = Field(default_factory=dict)

    def canonical_key(self) -> str:
        """Return the canonical instrument key."""
        return self.instrument_id
