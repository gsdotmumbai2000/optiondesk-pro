"""Strategy engine bootstrap."""

from pathlib import Path

from app.events.event_bus import EventBus
from app.strategy.cache.strategy_cache import StrategyCache
from app.strategy.engine.bundle import EngineBundle
from app.strategy.engine.strategy_engine import StrategyEngine
from app.strategy.optimization.framework import OptimizationFramework
from app.strategy.providers.bundle_factory import build_engine_bundle
from app.strategy.repository.sqlite_strategy_repository import SqliteStrategyRepository
from app.strategy.repository.strategy_repository import StrategyRepository
from app.strategy.services.strategy_service import StrategyService
from app.strategy.validation.strategy_validator import StrategyValidator


class StrategyProvider:
    """Wire strategy engine dependencies."""

    def __init__(
        self,
        event_bus: EventBus | None = None,
        engines: EngineBundle | None = None,
        data_directory: Path | None = None,
    ) -> None:
        """Initialize provider with optional injected engine bundle.

        Strategies persist to strategy.db when `data_directory` is given
        (the real application always provides one via build_engine_registry);
        otherwise falls back to the original in-memory-only repository, so
        existing callers/tests that construct StrategyProvider directly are
        unaffected.
        """
        self.engines = engines or build_engine_bundle(event_bus)
        self.engine = StrategyEngine(self.engines)
        self.validator = StrategyValidator()
        self.cache = StrategyCache()
        if data_directory is not None:
            self.repository = SqliteStrategyRepository(data_directory / "strategy.db")
            self.repository.initialize()
        else:
            self.repository = StrategyRepository()
        self.optimization = OptimizationFramework()
        self.service = StrategyService(
            self.engine,
            self.validator,
            self.cache,
            self.repository,
            event_bus,
        )
