"""Risk limit models."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class RiskLimitConfig:
    """Configurable risk limit thresholds."""

    max_delta: Decimal | None = None
    max_gamma: Decimal | None = None
    max_vega: Decimal | None = None
    max_loss: Decimal | None = None
    max_margin: Decimal | None = None
    max_position_size: int | None = None
    max_capital_exposure: Decimal | None = None


@dataclass(frozen=True, slots=True)
class RiskLimitWarning:
    """Warning when a risk limit is exceeded."""

    limit_name: str
    limit_value: Decimal
    actual_value: Decimal
    message: str
