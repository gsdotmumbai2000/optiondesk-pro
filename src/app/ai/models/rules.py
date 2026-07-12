"""Configurable recommendation rule."""

from dataclasses import dataclass
from decimal import Decimal

from app.ai.models.enums import RecommendationCategory, RecommendationPriority, RuleCondition


@dataclass(frozen=True, slots=True)
class RecommendationRule:
    """Configurable AI recommendation rule."""

    rule_id: str
    condition: RuleCondition
    threshold: Decimal
    category: RecommendationCategory
    priority: RecommendationPriority
    suggested_action: str
    enabled: bool = True
    custom_expression: str = ""
