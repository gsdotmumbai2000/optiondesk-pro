"""Greeks input validation."""

from app.calculation.context.calculation_context import CalculationContext
from app.greeks.exceptions import InvalidGreeksInput
from app.pricing.models.option_contract import OptionContract
from app.pricing.models.pricing_result import PricingResult


class GreeksValidator:
    """Validate Greeks calculation inputs."""

    def validate(
        self,
        context: CalculationContext,
        contract: OptionContract,
        pricing_result: PricingResult,
    ) -> None:
        """Validate input bundle."""
        if context.spot_price <= 0:
            raise InvalidGreeksInput("spot_price must be positive")
        if contract.strike <= 0:
            raise InvalidGreeksInput("strike must be positive")
        if context.volatility <= 0:
            raise InvalidGreeksInput("volatility must be positive")
        if pricing_result.theoretical_price < 0:
            raise InvalidGreeksInput("theoretical_price cannot be negative")
        if pricing_result.d1 is None or pricing_result.d2 is None:
            raise InvalidGreeksInput("pricing_result must include d1 and d2")
