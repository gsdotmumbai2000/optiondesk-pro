"""AI domain models."""

from app.ai.models.alternative import AlternativeStrategy
from app.ai.models.batch import RecommendationBatchResult
from app.ai.models.context import EngineContextSnapshot
from app.ai.models.enums import (
    AIModelVersion,
    EvidenceSource,
    LLMProviderType,
    PromptTemplateType,
    RecommendationCategory,
    RecommendationPriority,
    RuleCondition,
)
from app.ai.models.evidence import EvidenceMetric, SupportingEvidence
from app.ai.models.explanation import Explanation, TradeOff
from app.ai.models.memory import (
    PinnedRecommendation,
    RecommendationMemoryState,
    UserPreferences,
)
from app.ai.models.prompts import PromptTemplate, RenderedPrompt
from app.ai.models.request import RecommendationAnalysisRequest
from app.ai.models.result import RecommendationResult
from app.ai.models.rules import RecommendationRule
from app.ai.models.scoring import RecommendationScores

__all__ = [
    "AIModelVersion",
    "AlternativeStrategy",
    "EngineContextSnapshot",
    "EvidenceMetric",
    "EvidenceSource",
    "Explanation",
    "LLMProviderType",
    "PinnedRecommendation",
    "PromptTemplate",
    "PromptTemplateType",
    "RecommendationAnalysisRequest",
    "RecommendationBatchResult",
    "RecommendationCategory",
    "RecommendationMemoryState",
    "RecommendationPriority",
    "RecommendationResult",
    "RecommendationRule",
    "RecommendationScores",
    "RenderedPrompt",
    "RuleCondition",
    "SupportingEvidence",
    "TradeOff",
    "UserPreferences",
]
