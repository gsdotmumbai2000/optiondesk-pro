"""Backtest request bundle."""

from dataclasses import dataclass

from app.backtesting.models.config import SimulationParameters
from app.backtesting.models.historical import (
    HistoricalMarketData,
    HistoricalOptionChainData,
)
from app.strategy.models.context import StrategyContext
from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.models.result import OptimizationResult


@dataclass(frozen=True, slots=True)
class BacktestRequest:
    """Immutable input bundle for backtesting."""

    strategy: Strategy
    strategy_context: StrategyContext | None
    optimization_result: OptimizationResult | None
    market_data: HistoricalMarketData
    option_chain_data: HistoricalOptionChainData
    parameters: SimulationParameters
