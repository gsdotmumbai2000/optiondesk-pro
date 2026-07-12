"""Margin engine bootstrap."""

from app.events.event_bus import EventBus
from app.margin.adapters.broker_margin_provider import BrokerMarginProvider
from app.margin.adapters.estimated_margin_provider import EstimatedMarginProvider
from app.margin.cache.margin_cache import MarginCache
from app.margin.engine.margin_engine import MarginEngine
from app.margin.optimization.margin_optimizer import MarginOptimizer
from app.margin.services.capital_efficiency_service import CapitalEfficiencyService
from app.margin.services.margin_service import MarginService
from app.margin.validation.margin_validator import MarginValidator


class MarginProvider:
    """Wire margin engine dependencies."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize provider."""
        self.estimated_adapter = EstimatedMarginProvider()
        self.broker_adapter = BrokerMarginProvider(fallback=self.estimated_adapter)
        self.engine = MarginEngine()
        self.validator = MarginValidator()
        self.cache = MarginCache()
        self.optimizer = MarginOptimizer()
        self.capital_efficiency_service = CapitalEfficiencyService(self.optimizer)
        self.service = MarginService(
            self.engine,
            self.validator,
            self.cache,
            event_bus,
            self.optimizer,
        )
