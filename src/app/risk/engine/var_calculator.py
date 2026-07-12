"""VaR calculator."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.risk.analytics.var_historical import historical_var
from app.risk.analytics.var_parametric import parametric_var
from app.risk.analytics.var_variance_covariance import variance_covariance_var
from app.risk.models.enums import ConfidenceLevel
from app.risk.models.var import VaRResult
from app.volatility.models.volatility_result import VolatilityResult


class VaRCalculator:
    """Calculate VaR across methods and confidence levels."""

    def calculate_all(
        self,
        portfolio_value: Decimal,
        portfolio_volatility: Decimal,
        context: CalculationContext,
        volatility: VolatilityResult,
    ) -> tuple[VaRResult, ...]:
        """Return VaR for all methods at 95% and 99%."""
        levels = (ConfidenceLevel.P95, ConfidenceLevel.P99)
        results: list[VaRResult] = []
        for level in levels:
            results.append(parametric_var(portfolio_value, portfolio_volatility, level))
            results.append(historical_var(portfolio_value, context, volatility, level))
            results.append(
                variance_covariance_var(portfolio_value, portfolio_volatility, level)
            )
        return tuple(results)
