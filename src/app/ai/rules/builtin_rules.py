"""Built-in recommendation rules."""

from decimal import Decimal

from app.ai.models.enums import RecommendationCategory, RecommendationPriority, RuleCondition
from app.ai.models.rules import RecommendationRule
from app.utils.uuid_helper import generate_uuid


def default_rules() -> tuple[RecommendationRule, ...]:
    """Return default configurable rules."""
    return (
        _rule(
            RuleCondition.DELTA_EXCEEDS,
            Decimal("100"),
            RecommendationCategory.INCREASE_HEDGE,
            RecommendationPriority.HIGH,
            "Add delta hedge to reduce directional exposure",
        ),
        _rule(
            RuleCondition.MARGIN_UTILIZATION_EXCEEDS,
            Decimal("0.80"),
            RecommendationCategory.REDUCE_MARGIN,
            RecommendationPriority.URGENT,
            "Reduce positions or add capital to lower margin usage",
        ),
        _rule(
            RuleCondition.POP_BELOW,
            Decimal("0.40"),
            RecommendationCategory.POSITION_ADJUSTMENT,
            RecommendationPriority.MEDIUM,
            "Adjust strategy to improve probability of profit",
        ),
        _rule(
            RuleCondition.RISK_SCORE_EXCEEDS,
            Decimal("70"),
            RecommendationCategory.RISK_REDUCTION,
            RecommendationPriority.HIGH,
            "Reduce portfolio risk exposure",
        ),
        _rule(
            RuleCondition.LOSS_EXCEEDS,
            Decimal("-5000"),
            RecommendationCategory.REDUCE_LOSS,
            RecommendationPriority.URGENT,
            "Cut losses or hedge losing positions",
        ),
        _rule(
            RuleCondition.HEALTH_SCORE_BELOW,
            Decimal("50"),
            RecommendationCategory.RISK_REDUCTION,
            RecommendationPriority.HIGH,
            "Address monitor alerts to restore portfolio health",
        ),
    )


def _rule(
    condition: RuleCondition,
    threshold: Decimal,
    category: RecommendationCategory,
    priority: RecommendationPriority,
    action: str,
) -> RecommendationRule:
    return RecommendationRule(
        rule_id=generate_uuid(),
        condition=condition,
        threshold=threshold,
        category=category,
        priority=priority,
        suggested_action=action,
    )
