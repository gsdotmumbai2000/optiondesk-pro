"""Portfolio exposure models."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class UnderlyingExposure:
    """Exposure to a single underlying."""

    underlying: str
    notional: Decimal
    weight: Decimal


@dataclass(frozen=True, slots=True)
class ExpiryExposure:
    """Exposure by expiry date."""

    expiry: str
    notional: Decimal
    weight: Decimal


@dataclass(frozen=True, slots=True)
class OptionTypeExposure:
    """Exposure by option type."""

    option_type: str
    notional: Decimal
    weight: Decimal


@dataclass(frozen=True, slots=True)
class SectorExposure:
    """Exposure by sector (underlying grouping)."""

    sector: str
    notional: Decimal
    weight: Decimal


@dataclass(frozen=True, slots=True)
class PortfolioExposure:
    """Aggregate portfolio exposure breakdown."""

    total_notional: Decimal
    underlying: tuple[UnderlyingExposure, ...]
    expiry: tuple[ExpiryExposure, ...]
    option_type: tuple[OptionTypeExposure, ...]
    sector: tuple[SectorExposure, ...]
