"""Pricing result model."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.pricing.models.enums import ModelVersion


@dataclass(frozen=True, slots=True)
class PricingResult:
    """Immutable Black-Scholes pricing output."""

    theoretical_price: Decimal
    intrinsic_value: Decimal
    extrinsic_value: Decimal
    d1: Decimal
    d2: Decimal
    forward_price: Decimal
    discount_factor: Decimal
    calculation_time: datetime
    model_version: ModelVersion = ModelVersion.BLACK_SCHOLES_MERTON_V1
