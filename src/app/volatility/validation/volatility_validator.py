"""Volatility input validation."""

from app.calculation.context.calculation_context import CalculationContext
from app.greeks.models.greeks_result import GreeksResult
from app.pricing.models.pricing_result import PricingResult
from app.volatility.exceptions import InvalidVolatilityInput
from app.volatility.models.request import VolatilityAnalysisRequest


class VolatilityValidator:
    """Validate volatility analysis inputs."""

    def validate(self, request: VolatilityAnalysisRequest) -> None:
        """Validate request bundle."""
        self._validate_context(request.context)
        self._validate_pricing(request.pricing_result)
        self._validate_greeks(request.greeks_result)
        self._validate_snapshot(request.market_snapshot.snapshot_id)

    def _validate_context(self, context: CalculationContext) -> None:
        if context.spot_price <= 0:
            raise InvalidVolatilityInput("spot_price must be positive")

    def _validate_pricing(self, pricing: PricingResult) -> None:
        if pricing.theoretical_price < 0:
            raise InvalidVolatilityInput("theoretical_price cannot be negative")

    def _validate_greeks(self, greeks: GreeksResult) -> None:
        if greeks.delta is None:
            raise InvalidVolatilityInput("greeks_result must include delta")

    def _validate_snapshot(self, snapshot_id: str) -> None:
        if not snapshot_id:
            raise InvalidVolatilityInput("market_snapshot must include snapshot_id")
