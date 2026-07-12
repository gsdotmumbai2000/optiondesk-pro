"""Probability input validation."""

from app.calculation.context.calculation_context import CalculationContext
from app.greeks.models.greeks_result import GreeksResult
from app.option_chain.models.analysis import OptionChainAnalysis
from app.pricing.models.pricing_result import PricingResult
from app.probability.exceptions import InvalidProbabilityInput
from app.probability.models.request import ProbabilityAnalysisRequest
from app.volatility.models.volatility_result import VolatilityResult


class ProbabilityValidator:
    """Validate probability analysis inputs."""

    def validate(self, request: ProbabilityAnalysisRequest) -> None:
        """Validate request bundle."""
        self._validate_context(request.context)
        self._validate_pricing(request.pricing_result)
        self._validate_greeks(request.greeks_result)
        self._validate_volatility(request.volatility_result)
        self._validate_chain(request.chain_analysis)

    def _validate_context(self, context: CalculationContext) -> None:
        if context.spot_price <= 0:
            raise InvalidProbabilityInput("spot_price must be positive")

    def _validate_pricing(self, pricing: PricingResult) -> None:
        if pricing.theoretical_price < 0:
            raise InvalidProbabilityInput("theoretical_price cannot be negative")

    def _validate_greeks(self, greeks: GreeksResult) -> None:
        if greeks.delta is None:
            raise InvalidProbabilityInput("greeks_result must include delta")

    def _validate_volatility(self, volatility: VolatilityResult) -> None:
        if volatility.implied_volatility <= 0:
            raise InvalidProbabilityInput("implied_volatility must be positive")

    def _validate_chain(self, chain: OptionChainAnalysis) -> None:
        if chain.liquidity_score < 0:
            raise InvalidProbabilityInput("chain_analysis must include liquidity_score")
