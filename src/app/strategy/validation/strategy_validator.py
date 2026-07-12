"""Strategy input validation."""

from app.calculation.context.calculation_context import CalculationContext
from app.market_data.models.snapshot import MarketSnapshot
from app.strategy.exceptions import InvalidStrategyInput
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.request import StrategyEvaluationRequest
from app.strategy.models.strategy import Strategy


class StrategyValidator:
    """Validate strategy inputs."""

    def validate_strategy(self, strategy: Strategy) -> None:
        """Validate strategy definition."""
        if not strategy.legs:
            raise InvalidStrategyInput("strategy must have at least one leg")
        for leg in strategy.legs:
            self._validate_leg(leg)

    def validate_evaluation_request(self, request: StrategyEvaluationRequest) -> None:
        """Validate evaluation request."""
        self.validate_strategy(request.strategy)
        self._validate_context(request.calculation_context)
        self._validate_snapshot(request.market_snapshot)

    def _validate_leg(self, leg: StrategyLeg) -> None:
        if leg.quantity == 0:
            raise InvalidStrategyInput("leg quantity cannot be zero")
        if not leg.leg_id:
            raise InvalidStrategyInput("leg must have leg_id")

    def _validate_context(self, context: CalculationContext) -> None:
        if context.spot_price <= 0:
            raise InvalidStrategyInput("spot_price must be positive")

    def _validate_snapshot(self, snapshot: MarketSnapshot) -> None:
        if not snapshot.snapshot_id:
            raise InvalidStrategyInput("market_snapshot must include snapshot_id")
