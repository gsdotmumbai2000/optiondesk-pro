"""VaR application service."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.risk.analytics.expected_shortfall import expected_shortfall
from app.risk.engine.var_calculator import VaRCalculator
from app.risk.models.enums import ConfidenceLevel
from app.risk.models.var import CVaRResult, VaRResult
from app.volatility.models.volatility_result import VolatilityResult


class VaRService:
    """Service for VaR and CVaR calculations."""

    def __init__(self, calculator: VaRCalculator | None = None) -> None:
        """Initialize service."""
        self._calculator = calculator or VaRCalculator()

    def calculate_var(
        self,
        portfolio_value: Decimal,
        portfolio_volatility: Decimal,
        context: CalculationContext,
        volatility: VolatilityResult,
    ) -> tuple[VaRResult, ...]:
        """Calculate VaR across all methods."""
        return self._calculator.calculate_all(
            portfolio_value, portfolio_volatility, context, volatility
        )

    def calculate_cvar(
        self,
        var_results: tuple[VaRResult, ...],
        portfolio_volatility: Decimal,
    ) -> tuple[CVaRResult, ...]:
        """Calculate CVaR for each VaR result."""
        return tuple(
            expected_shortfall(v.value_at_risk, portfolio_volatility, v.confidence)
            for v in var_results
        )

    def primary_var(
        self,
        var_results: tuple[VaRResult, ...],
        confidence: ConfidenceLevel = ConfidenceLevel.P95,
    ) -> Decimal:
        """Return primary VaR at given confidence."""
        for result in var_results:
            if result.confidence == confidence:
                return result.value_at_risk
        return var_results[0].value_at_risk if var_results else Decimal("0")
