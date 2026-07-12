"""Volatility engine bootstrap."""

from app.events.event_bus import EventBus
from app.volatility.cache.volatility_cache import VolatilityCache
from app.volatility.engine.volatility_engine import VolatilityEngine
from app.volatility.services.volatility_service import VolatilityService
from app.volatility.validation.volatility_validator import VolatilityValidator


class VolatilityProvider:
    """Wire volatility engine dependencies."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize provider."""
        self.engine = VolatilityEngine()
        self.validator = VolatilityValidator()
        self.cache = VolatilityCache()
        self.service = VolatilityService(
            self.engine,
            self.validator,
            self.cache,
            event_bus,
        )
