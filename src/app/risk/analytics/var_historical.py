"""Historical VaR calculation."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.risk.analytics.z_scores import z_score
from app.risk.models.enums import ConfidenceLevel, VaRMethod
from app.risk.models.var import VaRResult
from app.volatility.models.volatility_result import VolatilityResult


def historical_var(
    portfolio_value: Decimal,
    context: CalculationContext,
    volatility: VolatilityResult,
    confidence: ConfidenceLevel,
) -> VaRResult:
    """Compute historical VaR using realized volatility."""
    hist_vol = volatility.historical_volatility.primary
    if hist_vol is None or hist_vol <= 0:
        hist_vol = context.historical_volatility
    if hist_vol is None or hist_vol <= 0:
        hist_vol = volatility.realized_volatility
    daily_vol = hist_vol / Decimal("15.8745")
    z = z_score(confidence)
    var = portfolio_value * daily_vol * z
    return VaRResult(
        method=VaRMethod.HISTORICAL,
        confidence=confidence,
        value_at_risk=var,
        portfolio_value=portfolio_value,
    )
