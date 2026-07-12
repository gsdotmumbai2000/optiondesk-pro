"""Recommendation domain model."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.monitor.models.enums import AlertPriority, RecommendationType


@dataclass(frozen=True, slots=True)
class Recommendation:
    """Framework recommendation (no AI)."""

    recommendation_id: str
    recommendation_type: RecommendationType
    symbol: str
    title: str
    rationale: str
    priority: AlertPriority
    suggested_action: str
    confidence: Decimal
    generated_at: datetime
