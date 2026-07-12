"""Quant engine bootstrap."""

from app.events.event_bus import EventBus
from app.quant.registry.engine_registry import QuantEngineRegistry
from app.quant.services.quant_service import QuantService
from app.strategy.engine.bundle import EngineBundle


class QuantProvider:
    """Wire quantitative engine integration layer."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize provider."""
        self.registry = QuantEngineRegistry(event_bus)
        self.service = QuantService(self.registry, event_bus)

    def build_engine_bundle(self) -> EngineBundle:
        """Build strategy-compatible engine bundle."""
        return self.service.build_engine_bundle()
