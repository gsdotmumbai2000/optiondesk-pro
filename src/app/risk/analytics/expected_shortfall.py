"""Expected Shortfall (CVaR) calculation."""

from decimal import Decimal

from app.risk.analytics.z_scores import z_score
from app.risk.models.enums import ConfidenceLevel
from app.risk.models.var import CVaRResult


def expected_shortfall(
    value_at_risk: Decimal,
    portfolio_volatility: Decimal,
    confidence: ConfidenceLevel,
) -> CVaRResult:
    """Compute conditional VaR and tail loss."""
    z = z_score(confidence)
    tail_factor = Decimal("1") + portfolio_volatility / (z * Decimal("2"))
    es = value_at_risk * tail_factor
    tail_loss = es - value_at_risk
    return CVaRResult(
        confidence=confidence,
        expected_shortfall=es,
        tail_loss=tail_loss,
    )
