"""Greeks calculator."""

from app.calculation.context.calculation_context import CalculationContext
from app.greeks.analytics.bs_greeks import calculate_bs_greeks
from app.greeks.models.greeks_result import GreeksResult
from app.pricing.models.option_contract import OptionContract
from app.pricing.models.pricing_result import PricingResult


class GreeksCalculator:
    """Calculate Greeks from pricing outputs."""

    def calculate(
        self,
        context: CalculationContext,
        contract: OptionContract,
        pricing_result: PricingResult,
    ) -> GreeksResult:
        """Compute GreeksResult from context, contract, and pricing."""
        return calculate_bs_greeks(context, contract, pricing_result)
