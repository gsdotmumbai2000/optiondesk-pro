"""Option chain input validation."""

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.models.snapshots import OptionChainSnapshot
from app.greeks.models.greeks_result import GreeksResult
from app.option_chain.exceptions import InvalidOptionChainInput
from app.option_chain.models.request import OptionChainAnalysisRequest
from app.volatility.models.volatility_result import VolatilityResult


class OptionChainValidator:
    """Validate option chain analysis inputs."""

    def validate(self, request: OptionChainAnalysisRequest) -> None:
        """Validate request bundle."""
        self._validate_context(request.context)
        self._validate_chain(request.option_chain)
        self._validate_greeks(request.greeks_result)
        self._validate_volatility(request.volatility_result)
        self._validate_snapshot(request.market_snapshot.snapshot_id)

    def _validate_context(self, context: CalculationContext) -> None:
        if context.spot_price <= 0:
            raise InvalidOptionChainInput("spot_price must be positive")

    def _validate_chain(self, chain: OptionChainSnapshot) -> None:
        if not chain.underlying.strip():
            raise InvalidOptionChainInput("option_chain must include underlying")

    def _validate_greeks(self, greeks: GreeksResult) -> None:
        if greeks.delta is None:
            raise InvalidOptionChainInput("greeks_result must include delta")

    def _validate_volatility(self, volatility: VolatilityResult) -> None:
        if volatility.implied_volatility <= 0:
            raise InvalidOptionChainInput("implied_volatility must be positive")

    def _validate_snapshot(self, snapshot_id: str) -> None:
        if not snapshot_id:
            raise InvalidOptionChainInput("market_snapshot must include snapshot_id")
