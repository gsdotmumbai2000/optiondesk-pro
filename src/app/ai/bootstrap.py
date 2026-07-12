"""AI recommendation engine bootstrap."""

from app.events.event_bus import EventBus
from app.ai.cache.recommendation_cache import RecommendationCache
from app.ai.engine.recommendation_engine import RecommendationEngine
from app.ai.memory.recommendation_memory import RecommendationMemory
from app.ai.providers.null_provider import NullLLMProvider
from app.ai.services.ai_recommendation_service import AIRecommendationService
from app.ai.services.explanation_service import ExplanationService
from app.ai.services.prompt_service import PromptService
from app.ai.services.rule_engine_service import RuleEngineService
from app.ai.validation.recommendation_validator import RecommendationValidator


class AIProvider:
    """Wire AI recommendation engine dependencies."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize provider."""
        self.engine = RecommendationEngine()
        self.validator = RecommendationValidator()
        self.cache = RecommendationCache()
        self.memory = RecommendationMemory()
        self.llm_provider = NullLLMProvider()
        self.rule_engine_service = RuleEngineService(validator=self.validator)
        self.explanation_service = ExplanationService()
        self.prompt_service = PromptService(llm_provider=self.llm_provider)
        self.service = AIRecommendationService(
            self.engine,
            self.validator,
            self.cache,
            self.memory,
            event_bus,
        )
