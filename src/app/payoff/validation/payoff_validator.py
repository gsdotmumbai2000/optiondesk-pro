"""Payoff input validation."""

from app.calculation.context.calculation_context import CalculationContext
from app.greeks.models.greeks_result import GreeksResult
from app.payoff.exceptions import InvalidPayoffInput
from app.payoff.models.legs import StrategyLeg
from app.payoff.models.request import PayoffAnalysisRequest
from app.pricing.models.pricing_result import PricingResult
from app.probability.models.probability_result import ProbabilityResult
from app.volatility.models.volatility_result import VolatilityResult


class PayoffValidator:
    """Validate payoff analysis inputs."""

    def validate(self, request: PayoffAnalysisRequest) -> None:
        """Validate request bundle."""
        self._validate_context(request.context)
        self._validate_pricing(request.pricing_result)
        self._validate_greeks(request.greeks_result)
        self._validate_volatility(request.volatility_result)
        self._validate_probability(request.probability_result)
        self._validate_legs(request.resolved_legs)

    def _validate_context(self, context: CalculationContext) -> None:
        if context.spot_price <= 0:
            raise InvalidPayoffInput("spot_price must be positive")

    def _validate_pricing(self, pricing: PricingResult) -> None:
        if pricing.theoretical_price < 0:
            raise InvalidPayoffInput("theoretical_price cannot be negative")

    def _validate_greeks(self, greeks: GreeksResult) -> None:
        if greeks.delta is None:
            raise InvalidPayoffInput("greeks_result must include delta")

    def _validate_volatility(self, volatility: VolatilityResult) -> None:
        if volatility.implied_volatility <= 0:
            raise InvalidPayoffInput("implied_volatility must be positive")

    def _validate_probability(self, probability: ProbabilityResult) -> None:
        if probability.expected_value is None:
            raise InvalidPayoffInput("probability_result must include expected_value")

    def _validate_legs(self, legs: tuple[StrategyLeg, ...]) -> None:
        if not legs:
            raise InvalidPayoffInput("portfolio must include at least one leg")
        for leg in legs:
            if leg.quantity == 0:
                raise InvalidPayoffInput("leg quantity cannot be zero")
