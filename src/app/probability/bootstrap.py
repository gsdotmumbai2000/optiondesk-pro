"""Probability engine bootstrap."""

from app.events.event_bus import EventBus
from app.probability.cache.probability_cache import ProbabilityCache
from app.probability.engine.probability_engine import ProbabilityEngine
from app.probability.services.probability_service import ProbabilityService
from app.probability.validation.probability_validator import ProbabilityValidator


class ProbabilityProvider:
    """Wire probability engine dependencies."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize provider."""
        self.engine = ProbabilityEngine()
        self.validator = ProbabilityValidator()
        self.cache = ProbabilityCache()
        self.service = ProbabilityService(
            self.engine,
            self.validator,
            self.cache,
            event_bus,
        )
