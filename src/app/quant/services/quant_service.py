"""Quant application service."""

from app.events.event_bus import EventBus
from app.quant.events import QuantBundleBuiltEvent, QuantEnginesInitializedEvent
from app.quant.models.bundle import QuantEngineProviders
from app.quant.providers.bundle_factory import build_strategy_engine_bundle
from app.quant.registry.engine_registry import QuantEngineRegistry
from app.strategy.engine.bundle import EngineBundle


class QuantService:
    """Orchestrate quantitative engine registration and bundle wiring."""

    def __init__(
        self,
        registry: QuantEngineRegistry,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize service."""
        self._registry = registry
        self._event_bus = event_bus
        self._publish_initialized()

    @property
    def providers(self) -> QuantEngineProviders:
        """Return quantitative engine providers."""
        return self._registry.providers

    def build_engine_bundle(self) -> EngineBundle:
        """Build strategy-compatible engine bundle."""
        bundle = build_strategy_engine_bundle(self.providers)
        if self._event_bus is not None:
            self._event_bus.publish(QuantBundleBuiltEvent(payload={}))
        return bundle

    def _publish_initialized(self) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(QuantEnginesInitializedEvent(payload={}))
