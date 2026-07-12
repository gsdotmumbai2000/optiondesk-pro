"""Strategy engine bootstrap."""

from app.events.event_bus import EventBus
from app.strategy.cache.strategy_cache import StrategyCache
from app.strategy.engine.bundle import EngineBundle
from app.strategy.engine.strategy_engine import StrategyEngine
from app.strategy.optimization.framework import OptimizationFramework
from app.strategy.providers.bundle_factory import build_engine_bundle
from app.strategy.repository.strategy_repository import StrategyRepository
from app.strategy.services.strategy_service import StrategyService
from app.strategy.validation.strategy_validator import StrategyValidator


class StrategyProvider:
    """Wire strategy engine dependencies."""

    def __init__(
        self,
        event_bus: EventBus | None = None,
        engines: EngineBundle | None = None,
    ) -> None:
        """Initialize provider with optional injected engine bundle."""
        self.engines = engines or build_engine_bundle(event_bus)
        self.engine = StrategyEngine(self.engines)
        self.validator = StrategyValidator()
        self.cache = StrategyCache()
        self.repository = StrategyRepository()
        self.optimization = OptimizationFramework()
        self.service = StrategyService(
            self.engine,
            self.validator,
            self.cache,
            self.repository,
            event_bus,
        )
