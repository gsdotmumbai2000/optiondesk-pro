"""Parametric VaR calculation."""

from decimal import Decimal

from app.risk.analytics.z_scores import z_score
from app.risk.models.enums import ConfidenceLevel, VaRMethod
from app.risk.models.var import VaRResult


def parametric_var(
    portfolio_value: Decimal,
    portfolio_volatility: Decimal,
    confidence: ConfidenceLevel,
) -> VaRResult:
    """Compute parametric (variance-normal) VaR."""
    z = z_score(confidence)
    var = portfolio_value * portfolio_volatility * z
    return VaRResult(
        method=VaRMethod.PARAMETRIC,
        confidence=confidence,
        value_at_risk=var,
        portfolio_value=portfolio_value,
    )
