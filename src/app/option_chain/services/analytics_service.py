"""Option chain analytics service."""

from app.events.event_bus import EventBus
from app.option_chain.cache.option_chain_cache import OptionChainCache
from app.option_chain.engine.option_chain_engine import OptionChainEngine
from app.option_chain.events import OptionChainAnalyzedEvent, OptionChainUpdatedEvent
from app.option_chain.exceptions import OptionChainException
from app.option_chain.models.analysis import OptionChainAnalysis
from app.option_chain.models.request import OptionChainAnalysisRequest
from app.option_chain.providers.cache_keys import build_cache_key
from app.option_chain.validation.option_chain_validator import OptionChainValidator


class OptionChainAnalyticsService:
    """Orchestrate option chain analytics, caching, and events."""

    def __init__(
        self,
        engine: OptionChainEngine,
        validator: OptionChainValidator | None = None,
        cache: OptionChainCache | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize service."""
        self._engine = engine
        self._validator = validator or OptionChainValidator()
        self._cache = cache or OptionChainCache()
        self._event_bus = event_bus

    @property
    def cache(self) -> OptionChainCache:
        """Return option chain cache."""
        return self._cache

    def analyze(self, request: OptionChainAnalysisRequest) -> OptionChainAnalysis:
        """Analyze and cache option chain metrics."""
        try:
            self._validator.validate(request)
            result = self._engine.analyze(request)
            key = build_cache_key(request)
            self._cache.put(key, result)
            self._publish_events(key)
            return result
        except OptionChainException:
            raise

    def get_latest(self, request: OptionChainAnalysisRequest) -> OptionChainAnalysis | None:
        """Return latest cached result."""
        return self._cache.get_latest(build_cache_key(request))

    def refresh(self, request: OptionChainAnalysisRequest) -> OptionChainAnalysis:
        """Invalidate and recalculate."""
        self._cache.invalidate(build_cache_key(request))
        return self.analyze(request)

    def _publish_events(self, key: str) -> None:
        if self._event_bus is None:
            return
        payload = {"key": key}
        self._event_bus.publish(OptionChainAnalyzedEvent(payload=payload))
        self._event_bus.publish(OptionChainUpdatedEvent(payload=payload))
