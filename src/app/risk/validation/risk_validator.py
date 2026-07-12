"""Risk input validation."""

from app.calculation.context.calculation_context import CalculationContext
from app.greeks.models.greeks_result import GreeksResult
from app.market_data.models.snapshot import MarketSnapshot
from app.payoff.models.legs import StrategyLeg
from app.payoff.models.result import PayoffResult
from app.pricing.models.pricing_result import PricingResult
from app.probability.models.probability_result import ProbabilityResult
from app.risk.exceptions import InvalidRiskInput
from app.risk.models.request import RiskAnalysisRequest
from app.volatility.models.volatility_result import VolatilityResult


class RiskValidator:
    """Validate risk analysis inputs."""

    def validate(self, request: RiskAnalysisRequest) -> None:
        """Validate request bundle."""
        self._validate_context(request.context)
        self._validate_pricing(request.pricing_result)
        self._validate_greeks(request.greeks_result)
        self._validate_volatility(request.volatility_result)
        self._validate_probability(request.probability_result)
        self._validate_payoff(request.payoff_result)
        self._validate_legs(request.resolved_legs)
        self._validate_snapshot(request.market_snapshot)

    def _validate_context(self, context: CalculationContext) -> None:
        if context.spot_price <= 0:
            raise InvalidRiskInput("spot_price must be positive")

    def _validate_pricing(self, pricing: PricingResult) -> None:
        if pricing.theoretical_price < 0:
            raise InvalidRiskInput("theoretical_price cannot be negative")

    def _validate_greeks(self, greeks: GreeksResult) -> None:
        if greeks.delta is None:
            raise InvalidRiskInput("greeks_result must include delta")

    def _validate_volatility(self, volatility: VolatilityResult) -> None:
        if volatility.implied_volatility <= 0:
            raise InvalidRiskInput("implied_volatility must be positive")

    def _validate_probability(self, probability: ProbabilityResult) -> None:
        if probability.expected_value is None:
            raise InvalidRiskInput("probability_result must include expected_value")

    def _validate_payoff(self, payoff: PayoffResult) -> None:
        if payoff.current_pnl is None:
            raise InvalidRiskInput("payoff_result must include current_pnl")

    def _validate_legs(self, legs: tuple[StrategyLeg, ...]) -> None:
        if not legs:
            raise InvalidRiskInput("portfolio must include at least one leg")

    def _validate_snapshot(self, snapshot: MarketSnapshot) -> None:
        if not snapshot.snapshot_id:
            raise InvalidRiskInput("market_snapshot must include snapshot_id")
