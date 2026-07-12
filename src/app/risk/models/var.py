"""VaR and CVaR models."""

from dataclasses import dataclass
from decimal import Decimal

from app.risk.models.enums import ConfidenceLevel, VaRMethod


@dataclass(frozen=True, slots=True)
class VaRResult:
    """Value-at-Risk result for a single method."""

    method: VaRMethod
    confidence: ConfidenceLevel
    value_at_risk: Decimal
    portfolio_value: Decimal


@dataclass(frozen=True, slots=True)
class CVaRResult:
    """Conditional VaR (Expected Shortfall) result."""

    confidence: ConfidenceLevel
    expected_shortfall: Decimal
    tail_loss: Decimal
