"""Greeks result model."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.greeks.models.enums import GreeksModelVersion


@dataclass(frozen=True, slots=True)
class GreeksResult:
    """Immutable Black-Scholes Greeks output."""

    delta: Decimal
    gamma: Decimal
    theta: Decimal
    vega: Decimal
    rho: Decimal
    vanna: Decimal
    charm: Decimal
    vomma: Decimal
    calculation_timestamp: datetime
    model_version: GreeksModelVersion = GreeksModelVersion.BLACK_SCHOLES_V1
