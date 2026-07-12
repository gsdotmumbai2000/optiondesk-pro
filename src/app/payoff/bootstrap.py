"""Payoff engine bootstrap."""

from app.events.event_bus import EventBus
from app.payoff.cache.payoff_cache import PayoffCache
from app.payoff.engine.payoff_engine import PayoffEngine
from app.payoff.services.payoff_service import PayoffService
from app.payoff.validation.payoff_validator import PayoffValidator


class PayoffProvider:
    """Wire payoff engine dependencies."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize provider."""
        self.engine = PayoffEngine()
        self.validator = PayoffValidator()
        self.cache = PayoffCache()
        self.service = PayoffService(
            self.engine,
            self.validator,
            self.cache,
            event_bus,
        )
