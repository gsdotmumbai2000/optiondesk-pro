"""Volatility result models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.volatility.models.enums import VolatilityModelVersion


@dataclass(frozen=True, slots=True)
class HistoricalVolatility:
    """Historical volatility metrics."""

    primary: Decimal | None
    short_term: Decimal | None = None
    long_term: Decimal | None = None


@dataclass(frozen=True, slots=True)
class ExpectedMove:
    """Expected price move estimates."""

    to_expiry: Decimal
    one_day: Decimal | None = None


@dataclass(frozen=True, slots=True)
class VolatilityResult:
    """Immutable volatility analytics output."""

    implied_volatility: Decimal
    annualized_volatility: Decimal
    realized_volatility: Decimal
    historical_volatility: HistoricalVolatility
    expected_move: ExpectedMove
    iv_percentile: Decimal
    calculation_timestamp: datetime
    model_version: VolatilityModelVersion = VolatilityModelVersion.V1
