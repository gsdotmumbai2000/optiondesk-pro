"""Recommendation result model."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.ai.models.alternative import AlternativeStrategy
from app.ai.models.enums import AIModelVersion, RecommendationCategory, RecommendationPriority
from app.ai.models.evidence import SupportingEvidence
from app.ai.models.explanation import Explanation
from app.ai.models.scoring import RecommendationScores


@dataclass(frozen=True, slots=True)
class RecommendationResult:
    """Immutable AI recommendation output."""

    recommendation_id: str
    category: RecommendationCategory
    priority: RecommendationPriority
    confidence: Decimal
    summary: str
    detailed_explanation: Explanation
    supporting_evidence: SupportingEvidence
    suggested_action: str
    alternative_strategies: tuple[AlternativeStrategy, ...]
    expected_benefit: str
    expected_risk: str
    estimated_pop: Decimal
    capital_impact: Decimal
    risk_impact: Decimal
    margin_impact: Decimal
    confidence_score: Decimal
    scores: RecommendationScores
    warnings: tuple[str, ...]
    timestamp: datetime
    model_version: AIModelVersion = AIModelVersion.V1
