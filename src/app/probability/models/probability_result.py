"""Probability result model."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.probability.models.enums import ProbabilityModelVersion


@dataclass(frozen=True, slots=True)
class ProbabilityResult:
    """Immutable probability analytics output."""

    expected_value: Decimal
    probability_of_profit: Decimal
    probability_of_touch: Decimal | None = None
    calculation_timestamp: datetime | None = None
    model_version: ProbabilityModelVersion = ProbabilityModelVersion.V1
