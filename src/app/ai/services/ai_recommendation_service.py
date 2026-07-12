"""AI recommendation application service."""

from app.events.event_bus import EventBus
from app.ai.cache.recommendation_cache import RecommendationCache
from app.ai.engine.recommendation_engine import RecommendationEngine
from app.ai.events import (
    RecommendationAcceptedEvent,
    RecommendationDismissedEvent,
    RecommendationGeneratedEvent,
)
from app.ai.exceptions import AIException
from app.ai.memory.recommendation_memory import RecommendationMemory
from app.ai.models.batch import RecommendationBatchResult
from app.ai.models.request import RecommendationAnalysisRequest
from app.ai.models.result import RecommendationResult
from app.ai.providers.cache_keys import build_cache_key
from app.ai.validation.recommendation_validator import RecommendationValidator


class AIRecommendationService:
    """Orchestrate AI recommendations, caching, memory, and events."""

    def __init__(
        self,
        engine: RecommendationEngine,
        validator: RecommendationValidator | None = None,
        cache: RecommendationCache | None = None,
        memory: RecommendationMemory | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize service."""
        self._engine = engine
        self._validator = validator or RecommendationValidator()
        self._cache = cache or RecommendationCache()
        self._memory = memory or RecommendationMemory()
        self._event_bus = event_bus

    @property
    def cache(self) -> RecommendationCache:
        """Return recommendation cache."""
        return self._cache

    @property
    def memory(self) -> RecommendationMemory:
        """Return recommendation memory."""
        return self._memory

    def generate(
        self,
        request: RecommendationAnalysisRequest,
    ) -> RecommendationBatchResult:
        """Generate and cache AI recommendations."""
        try:
            self._validator.validate_request(request)
            result = self._engine.generate(request)
            for rec in result.recommendations:
                self._validator.validate_result(rec)
            key = build_cache_key(request)
            self._cache.put(key, result)
            self._memory.record(result.recommendations)
            self._publish_generated(key, result)
            return result
        except AIException:
            raise

    def get_latest(
        self,
        request: RecommendationAnalysisRequest,
    ) -> RecommendationBatchResult | None:
        """Return latest cached batch."""
        return self._cache.get_latest(build_cache_key(request))

    def refresh(
        self,
        request: RecommendationAnalysisRequest,
    ) -> RecommendationBatchResult:
        """Invalidate and regenerate."""
        self._cache.invalidate(build_cache_key(request))
        return self.generate(request)

    def dismiss(
        self,
        request: RecommendationAnalysisRequest,
        recommendation_id: str,
    ) -> None:
        """Dismiss recommendation."""
        key = build_cache_key(request)
        self._cache.dismiss(key, recommendation_id)
        self._memory.dismiss(recommendation_id)
        self._publish_dismissed(recommendation_id)

    def accept(
        self,
        request: RecommendationAnalysisRequest,
        recommendation_id: str,
    ) -> None:
        """Accept recommendation."""
        key = build_cache_key(request)
        self._cache.accept(key, recommendation_id)
        self._memory.accept(recommendation_id)
        self._publish_accepted(recommendation_id)

    def primary(
        self,
        batch: RecommendationBatchResult,
    ) -> RecommendationResult | None:
        """Return primary recommendation from batch."""
        return batch.primary

    def _publish_generated(self, key: str, result: RecommendationBatchResult) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            RecommendationGeneratedEvent(
                payload={"key": key, "count": str(len(result.recommendations))}
            )
        )

    def _publish_accepted(self, recommendation_id: str) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            RecommendationAcceptedEvent(
                payload={"recommendation_id": recommendation_id}
            )
        )

    def _publish_dismissed(self, recommendation_id: str) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            RecommendationDismissedEvent(
                payload={"recommendation_id": recommendation_id}
            )
        )
