"""Batch output from recommendation engine."""

from dataclasses import dataclass
from datetime import datetime

from app.ai.models.enums import AIModelVersion
from app.ai.models.result import RecommendationResult


@dataclass(frozen=True, slots=True)
class RecommendationBatchResult:
    """Collection of AI recommendations."""

    recommendations: tuple[RecommendationResult, ...]
    primary: RecommendationResult | None
    calculation_timestamp: datetime
    model_version: AIModelVersion = AIModelVersion.V1
