"""Backtest input validation."""

from app.backtesting.exceptions import InvalidBacktestInput
from app.backtesting.models.request import BacktestRequest
from app.strategy.models.strategy import Strategy


class BacktestValidator:
    """Validate backtest inputs."""

    def validate(self, request: BacktestRequest) -> None:
        """Validate request bundle."""
        self._validate_strategy(request.strategy)
        self._validate_market_data(request)
        self._validate_parameters(request)

    def _validate_strategy(self, strategy: Strategy) -> None:
        if not strategy.legs:
            raise InvalidBacktestInput("strategy must have at least one leg")

    def _validate_market_data(self, request: BacktestRequest) -> None:
        if not request.market_data.bars:
            raise InvalidBacktestInput("historical market data must include bars")

    def _validate_parameters(self, request: BacktestRequest) -> None:
        if request.parameters.initial_capital <= 0:
            raise InvalidBacktestInput("initial_capital must be positive")
