"""Configurable recommendation rule engine."""

from app.ai.models.context import EngineContextSnapshot
from app.ai.models.rules import RecommendationRule
from app.ai.models.request import RecommendationAnalysisRequest


class RecommendationRuleEngine:
    """Evaluate configurable rules against engine context."""

    def evaluate(
        self,
        request: RecommendationAnalysisRequest,
        context: EngineContextSnapshot,
        rules: tuple[RecommendationRule, ...],
    ) -> tuple[RecommendationRule, ...]:
        """Return rules that match current context."""
        matched: list[RecommendationRule] = []
        for rule in rules:
            if self._matches(rule, context, request):
                matched.append(rule)
        return tuple(matched)

    def _matches(
        self,
        rule: RecommendationRule,
        ctx: EngineContextSnapshot,
        request: RecommendationAnalysisRequest,
    ) -> bool:
        from app.ai.models.enums import RuleCondition

        checks = {
            RuleCondition.DELTA_EXCEEDS: abs(ctx.net_delta) >= rule.threshold,
            RuleCondition.MARGIN_UTILIZATION_EXCEEDS: (
                ctx.margin_utilization >= rule.threshold
            ),
            RuleCondition.POP_BELOW: ctx.probability_of_profit <= rule.threshold,
            RuleCondition.RISK_SCORE_EXCEEDS: ctx.risk_score >= rule.threshold,
            RuleCondition.LOSS_EXCEEDS: ctx.unrealized_pnl <= rule.threshold,
            RuleCondition.MARGIN_AVAILABLE_BELOW: (
                ctx.available_margin <= rule.threshold
            ),
            RuleCondition.HEALTH_SCORE_BELOW: ctx.health_score <= rule.threshold,
            RuleCondition.CUSTOM: bool(rule.custom_expression),
        }
        return checks.get(rule.condition, False)
