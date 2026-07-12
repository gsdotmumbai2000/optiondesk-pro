"""Alternative strategy model."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class AlternativeStrategy:
    """Alternative strategy suggestion from optimization engine."""

    strategy_id: str
    label: str
    expected_return: Decimal
    probability_of_profit: Decimal
    capital_required: Decimal
    rationale: str
