"""Option contract model."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.pricing.models.enums import ExerciseStyle, OptionType


@dataclass(frozen=True, slots=True)
class OptionContract:
    """Immutable European option contract definition."""

    strike: Decimal
    option_type: OptionType
    expiry: date
    exercise_style: ExerciseStyle = ExerciseStyle.EUROPEAN
    multiplier: int = 1
