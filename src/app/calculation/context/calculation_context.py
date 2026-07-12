"""Immutable calculation context."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from app.calculation.models.configuration import CalculationConfiguration
from app.calculation.models.enums import ContextVersion
from app.calculation.models.market_session import MarketSession
from app.calculation.models.snapshots import (
    FutureQuoteSnapshot,
    OptionChainSnapshot,
    SpotQuoteSnapshot,
)


@dataclass(frozen=True, slots=True)
class CalculationContext:
    """Immutable input bundle for all downstream calculations."""

    underlying: str
    spot_price: Decimal
    future_price: Decimal | None
    underlying_symbol: str
    exchange: str
    expiry: date
    current_time: datetime
    trade_date: date
    market_status: str
    interest_rate: Decimal
    dividend_yield: Decimal
    risk_free_rate: Decimal
    volatility: Decimal
    historical_volatility: Decimal | None
    implied_volatility: Decimal | None
    days_to_expiry: int
    time_to_expiry: Decimal
    atm_strike: Decimal
    lot_size: int
    tick_size: Decimal
    strike_interval: Decimal
    currency: str
    market_session: MarketSession
    option_chain_snapshot: OptionChainSnapshot | None
    future_quote: FutureQuoteSnapshot | None
    spot_quote: SpotQuoteSnapshot
    configuration: CalculationConfiguration
    calculation_timestamp: datetime
    version: ContextVersion = ContextVersion.V1
