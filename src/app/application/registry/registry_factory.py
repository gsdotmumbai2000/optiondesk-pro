"""Build engine registry from event bus."""

from pathlib import Path

from app.ai.bootstrap import AIProvider
from app.application.registry.engine_registry import EngineRegistry
from app.backtesting.bootstrap import BacktestProvider
from app.events.event_bus import EventBus
from app.market.bootstrap import MarketMasterProvider
from app.market_data.bootstrap import MarketDataProvider
from app.monitor.bootstrap import MonitorProvider
from app.portfolio.bootstrap import PortfolioProvider
from app.strategy.bootstrap import StrategyProvider
from app.strategy_optimizer.bootstrap import OptimizerProvider
from app.utils.constants import RESOURCES_DIR


def build_engine_registry(
    event_bus: EventBus | None = None,
    market_data: MarketDataProvider | None = None,
    data_directory: Path | None = None,
) -> EngineRegistry:
    """Wire all frozen engine providers."""
    data_dir = data_directory or (RESOURCES_DIR / "data")
    return EngineRegistry(
        strategy=StrategyProvider(event_bus),
        optimizer=OptimizerProvider(event_bus),
        backtest=BacktestProvider(event_bus),
        portfolio=PortfolioProvider(event_bus),
        monitor=MonitorProvider(event_bus),
        ai=AIProvider(event_bus),
        market_master=MarketMasterProvider(data_dir, event_bus),
        market_data=market_data,
    )
