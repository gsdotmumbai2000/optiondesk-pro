"""Margin input validation."""

from app.calculation.context.calculation_context import CalculationContext
from app.market_data.models.snapshot import MarketSnapshot
from app.margin.exceptions import InvalidMarginInput
from app.margin.models.request import MarginAnalysisRequest
from app.payoff.models.legs import StrategyLeg
from app.payoff.models.result import PayoffResult
from app.risk.models.result import RiskResult


class MarginValidator:
    """Validate margin analysis inputs."""

    def validate(self, request: MarginAnalysisRequest) -> None:
        """Validate request bundle."""
        self._validate_context(request.context)
        self._validate_legs(request.resolved_legs)
        self._validate_risk(request.risk_result)
        self._validate_payoff(request.payoff_result)
        self._validate_snapshot(request.market_snapshot)

    def _validate_context(self, context: CalculationContext) -> None:
        if context.spot_price <= 0:
            raise InvalidMarginInput("spot_price must be positive")
        if context.lot_size <= 0:
            raise InvalidMarginInput("lot_size must be positive")

    def _validate_legs(self, legs: tuple[StrategyLeg, ...]) -> None:
        if not legs:
            raise InvalidMarginInput("portfolio must include at least one leg")
        for leg in legs:
            if leg.quantity == 0:
                raise InvalidMarginInput("leg quantity cannot be zero")

    def _validate_risk(self, risk: RiskResult) -> None:
        if risk.capital_at_risk < 0:
            raise InvalidMarginInput("capital_at_risk cannot be negative")

    def _validate_payoff(self, payoff: PayoffResult) -> None:
        if payoff.current_pnl is None:
            raise InvalidMarginInput("payoff_result must include current_pnl")

    def _validate_snapshot(self, snapshot: MarketSnapshot) -> None:
        if not snapshot.snapshot_id:
            raise InvalidMarginInput("market_snapshot must include snapshot_id")
