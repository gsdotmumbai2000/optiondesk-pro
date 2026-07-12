"""Optimizer input validation."""

from app.calculation.context.calculation_context import CalculationContext
from app.market_data.models.snapshot import MarketSnapshot
from app.strategy_optimizer.exceptions import InvalidOptimizerInput
from app.strategy_optimizer.models.preferences import OptimizationPreferences
from app.strategy_optimizer.models.request import OptimizationRequest


class OptimizerValidator:
    """Validate optimization inputs."""

    def validate(self, request: OptimizationRequest) -> None:
        """Validate request bundle."""
        self._validate_context(request.calculation_context)
        self._validate_preferences(request.preferences)
        self._validate_snapshot(request.market_snapshot)

    def _validate_context(self, context: CalculationContext) -> None:
        if context.spot_price <= 0:
            raise InvalidOptimizerInput("spot_price must be positive")

    def _validate_preferences(self, preferences: OptimizationPreferences) -> None:
        if preferences.capital <= 0:
            raise InvalidOptimizerInput("capital must be positive")
        if preferences.max_candidates <= 0:
            raise InvalidOptimizerInput("max_candidates must be positive")

    def _validate_snapshot(self, snapshot: MarketSnapshot) -> None:
        if not snapshot.snapshot_id:
            raise InvalidOptimizerInput("market_snapshot must include snapshot_id")
