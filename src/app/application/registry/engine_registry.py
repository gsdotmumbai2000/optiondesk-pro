"""Frozen engine provider registry."""

from dataclasses import dataclass

from app.ai.bootstrap import AIProvider
from app.backtesting.bootstrap import BacktestProvider
from app.market.bootstrap import MarketMasterProvider
from app.market_data.bootstrap import MarketDataProvider
from app.monitor.bootstrap import MonitorProvider
from app.portfolio.bootstrap import PortfolioProvider
from app.strategy.bootstrap import StrategyProvider
from app.strategy_optimizer.bootstrap import OptimizerProvider


@dataclass(frozen=True, slots=True)
class EngineRegistry:
    """Container for frozen engine providers (dependency injection)."""

    strategy: StrategyProvider
    optimizer: OptimizerProvider
    backtest: BacktestProvider
    portfolio: PortfolioProvider
    monitor: MonitorProvider
    ai: AIProvider
    market_master: MarketMasterProvider
    market_data: MarketDataProvider | None = None
