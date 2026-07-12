"""Option chain engine bootstrap."""

from app.events.event_bus import EventBus
from app.option_chain.cache.option_chain_cache import OptionChainCache
from app.option_chain.engine.option_chain_engine import OptionChainEngine
from app.option_chain.services.analytics_service import OptionChainAnalyticsService
from app.option_chain.validation.option_chain_validator import OptionChainValidator


class OptionChainProvider:
    """Wire option chain engine dependencies."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize provider."""
        self.engine = OptionChainEngine()
        self.validator = OptionChainValidator()
        self.cache = OptionChainCache()
        self.service = OptionChainAnalyticsService(
            self.engine,
            self.validator,
            self.cache,
            event_bus,
        )
