"""Variance-covariance VaR calculation."""

from decimal import Decimal

from app.risk.analytics.z_scores import z_score
from app.risk.models.enums import ConfidenceLevel, VaRMethod
from app.risk.models.var import VaRResult


def variance_covariance_var(
    portfolio_value: Decimal,
    portfolio_volatility: Decimal,
    confidence: ConfidenceLevel,
) -> VaRResult:
    """Compute variance-covariance VaR (single-factor)."""
    z = z_score(confidence)
    daily_vol = portfolio_volatility / Decimal("15.8745")
    var = portfolio_value * daily_vol * z
    return VaRResult(
        method=VaRMethod.VARIANCE_COVARIANCE,
        confidence=confidence,
        value_at_risk=var,
        portfolio_value=portfolio_value,
    )
