"""Greeks engine bootstrap."""

from app.events.event_bus import EventBus
from app.greeks.cache.greeks_cache import GreeksCache
from app.greeks.engine.greeks_engine import GreeksEngine
from app.greeks.services.greeks_service import GreeksService
from app.greeks.validation.greeks_validator import GreeksValidator


class GreeksProvider:
    """Wire Greeks engine dependencies."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize provider."""
        self.engine = GreeksEngine()
        self.validator = GreeksValidator()
        self.cache = GreeksCache()
        self.service = GreeksService(
            self.engine,
            self.validator,
            self.cache,
            event_bus,
        )
