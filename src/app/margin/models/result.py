"""Margin analysis result."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.margin.models.enums import MarginModelVersion, MarginSource


@dataclass(frozen=True, slots=True)
class MarginResult:
    """Immutable margin analytics output."""

    initial_margin: Decimal
    exposure_margin: Decimal
    span_margin: Decimal
    portfolio_margin: Decimal
    additional_margin: Decimal
    peak_margin: Decimal
    total_margin: Decimal
    available_margin: Decimal
    margin_utilization: Decimal
    buying_power: Decimal
    capital_required: Decimal
    capital_efficiency: Decimal
    leverage_ratio: Decimal
    margin_benefit: Decimal
    margin_reduction: Decimal
    margin_source: MarginSource
    calculation_timestamp: datetime
    model_version: MarginModelVersion = MarginModelVersion.V1
