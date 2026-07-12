"""Z-score lookup for VaR confidence levels."""

from decimal import Decimal

from app.risk.models.enums import ConfidenceLevel

_Z_SCORES: dict[ConfidenceLevel, Decimal] = {
    ConfidenceLevel.P95: Decimal("1.645"),
    ConfidenceLevel.P99: Decimal("2.326"),
}


def z_score(confidence: ConfidenceLevel) -> Decimal:
    """Return z-score for confidence level."""
    return _Z_SCORES[confidence]
