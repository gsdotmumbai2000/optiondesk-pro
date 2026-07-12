"""Greeks engine entry point."""

from app.calculation.context.calculation_context import CalculationContext
from app.greeks.engine.greeks_calculator import GreeksCalculator
from app.greeks.models.greeks_result import GreeksResult
from app.pricing.models.option_contract import OptionContract
from app.pricing.models.pricing_result import PricingResult


class GreeksEngine:
    """Enterprise Greeks engine."""

    def __init__(self, calculator: GreeksCalculator | None = None) -> None:
        """Initialize engine."""
        self._calculator = calculator or GreeksCalculator()

    @property
    def calculator(self) -> GreeksCalculator:
        """Return Greeks calculator."""
        return self._calculator

    def calculate_greeks(
        self,
        context: CalculationContext,
        contract: OptionContract,
        pricing_result: PricingResult,
    ) -> GreeksResult:
        """Calculate option Greeks."""
        return self._calculator.calculate(context, contract, pricing_result)
