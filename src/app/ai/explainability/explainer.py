"""Recommendation explanation builder."""

from app.ai.models.context import EngineContextSnapshot
from app.ai.models.evidence import SupportingEvidence
from app.ai.models.explanation import Explanation, TradeOff
from app.ai.models.rules import RecommendationRule


class ExplanationBuilder:
    """Build mandatory explanations for every recommendation."""

    def build(
        self,
        rule: RecommendationRule,
        context: EngineContextSnapshot,
        evidence: SupportingEvidence,
    ) -> Explanation:
        """Create full explanation from rule and evidence."""
        why = self._why(rule, context)
        return Explanation(
            why=why,
            supporting_data=evidence.summary,
            affected_metrics=evidence.affected_metrics,
            trade_offs=self._trade_offs(rule),
            potential_risks=self._risks(rule, context),
            potential_rewards=self._rewards(rule, context),
        )

    def _why(self, rule: RecommendationRule, ctx: EngineContextSnapshot) -> str:
        return (
            f"{rule.category.value}: {rule.condition.value} threshold "
            f"{rule.threshold} breached given current portfolio state "
            f"(PnL={ctx.unrealized_pnl}, risk_score={ctx.risk_score})."
        )

    def _trade_offs(self, rule: RecommendationRule) -> tuple[TradeOff, ...]:
        return (
            TradeOff(
                benefit=f"Addresses {rule.category.value} objective",
                risk="May reduce upside if market moves favorably",
            ),
        )

    def _risks(
        self,
        rule: RecommendationRule,
        ctx: EngineContextSnapshot,
    ) -> tuple[str, ...]:
        risks = [f"Current risk score is {ctx.risk_score}"]
        if ctx.critical_alert_count:
            risks.append(f"{ctx.critical_alert_count} critical monitor alerts active")
        return tuple(risks)

    def _rewards(
        self,
        rule: RecommendationRule,
        ctx: EngineContextSnapshot,
    ) -> tuple[str, ...]:
        return (
            f"Executing '{rule.suggested_action}' may improve portfolio health",
            f"Target margin utilization below {rule.threshold}",
        )
