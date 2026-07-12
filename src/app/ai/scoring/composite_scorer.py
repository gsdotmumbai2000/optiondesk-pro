"""Recommendation scoring calculators."""

from decimal import Decimal

from app.ai.models.context import EngineContextSnapshot
from app.ai.models.enums import RecommendationPriority
from app.ai.models.rules import RecommendationRule
from app.ai.models.scoring import RecommendationScores


class CompositeScorer:
    """Compute composite recommendation scores."""

    def score(
        self,
        rule: RecommendationRule,
        context: EngineContextSnapshot,
    ) -> RecommendationScores:
        """Build score bundle from engine context."""
        confidence = self._confidence(rule, context)
        impact = self._impact(rule, context)
        risk = min(context.risk_score, Decimal("100"))
        capital = self._capital_score(context)
        liquidity = self._liquidity_score(context)
        priority = self._priority_score(rule.priority)
        return RecommendationScores(
            confidence_score=confidence,
            impact_score=impact,
            risk_score=risk,
            capital_score=capital,
            liquidity_score=liquidity,
            priority_score=priority,
        )

    def _confidence(self, rule: RecommendationRule, ctx: EngineContextSnapshot) -> Decimal:
        base = Decimal("0.6")
        if rule.condition.value.startswith("MARGIN"):
            gap = ctx.margin_utilization - rule.threshold
            return min(base + gap * Decimal("2"), Decimal("0.95"))
        if rule.condition.value.startswith("DELTA"):
            gap = abs(ctx.net_delta) - rule.threshold
            return min(base + gap / Decimal("200"), Decimal("0.95"))
        return base + Decimal("0.15")

    def _impact(self, rule: RecommendationRule, ctx: EngineContextSnapshot) -> Decimal:
        if ctx.critical_alert_count > 0:
            return Decimal("90")
        if abs(ctx.unrealized_pnl) > abs(rule.threshold):
            return Decimal("75")
        return Decimal("50")

    def _capital_score(self, ctx: EngineContextSnapshot) -> Decimal:
        if ctx.portfolio_value <= 0:
            return Decimal("0")
        ratio = ctx.available_margin / ctx.portfolio_value
        return min(ratio * Decimal("100"), Decimal("100"))

    def _liquidity_score(self, ctx: EngineContextSnapshot) -> Decimal:
        if ctx.cash_balance <= 0:
            return Decimal("20")
        ratio = ctx.cash_balance / max(ctx.portfolio_value, Decimal("1"))
        return min(ratio * Decimal("100"), Decimal("100"))

    def _priority_score(self, priority: RecommendationPriority) -> Decimal:
        return {
            RecommendationPriority.LOW: Decimal("25"),
            RecommendationPriority.MEDIUM: Decimal("50"),
            RecommendationPriority.HIGH: Decimal("75"),
            RecommendationPriority.URGENT: Decimal("95"),
        }.get(priority, Decimal("50"))
