"""Strategy evaluation request builder."""

from app.strategy.models.request import StrategyEvaluationRequest
from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.models.request import OptimizationRequest


def build_evaluation_request(
    strategy: Strategy,
    request: OptimizationRequest,
) -> StrategyEvaluationRequest:
    """Build strategy evaluation request from optimization request."""
    return StrategyEvaluationRequest(
        strategy=strategy,
        calculation_context=request.calculation_context,
        option_contract=request.option_contract,
        option_chain=request.option_chain,
        market_snapshot=request.market_snapshot,
        chain_market_snapshot=request.chain_market_snapshot,
        volatility_market_snapshot=request.volatility_market_snapshot,
        historical_data=request.historical_data,
    )
