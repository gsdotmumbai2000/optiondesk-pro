"""Recommendation generator from matched rules."""

from datetime import datetime, timezone
from decimal import Decimal

from app.ai.explainability.evidence_builder import EvidenceBuilder
from app.ai.explainability.explainer import ExplanationBuilder
from app.ai.models.context import EngineContextSnapshot
from app.ai.models.request import RecommendationAnalysisRequest
from app.ai.models.result import RecommendationResult
from app.ai.models.rules import RecommendationRule
from app.ai.recommendations.alternatives import AlternativeStrategyBuilder
from app.ai.scoring.composite_scorer import CompositeScorer
from app.utils.uuid_helper import generate_uuid


class RecommendationGenerator:
    """Generate RecommendationResult from matched rules."""

    def __init__(self) -> None:
        """Initialize generator components."""
        self._evidence = EvidenceBuilder()
        self._explainer = ExplanationBuilder()
        self._scorer = CompositeScorer()
        self._alternatives = AlternativeStrategyBuilder()

    def generate(
        self,
        request: RecommendationAnalysisRequest,
        context: EngineContextSnapshot,
        matched_rules: tuple[RecommendationRule, ...],
    ) -> tuple[RecommendationResult, ...]:
        """Build recommendations with mandatory evidence."""
        results: list[RecommendationResult] = []
        alts = self._alternatives.build(request)
        for rule in matched_rules:
            evidence = self._evidence.build(request, context, rule)
            explanation = self._explainer.build(rule, context, evidence)
            scores = self._scorer.score(rule, context)
            results.append(
                RecommendationResult(
                    recommendation_id=generate_uuid(),
                    category=rule.category,
                    priority=rule.priority,
                    confidence=scores.confidence_score,
                    summary=f"{rule.category.value}: {rule.suggested_action}",
                    detailed_explanation=explanation,
                    supporting_evidence=evidence,
                    suggested_action=rule.suggested_action,
                    alternative_strategies=alts,
                    expected_benefit=explanation.potential_rewards[0],
                    expected_risk=explanation.potential_risks[0],
                    estimated_pop=context.probability_of_profit,
                    capital_impact=context.available_margin,
                    risk_impact=context.risk_score,
                    margin_impact=context.margin_utilization,
                    confidence_score=scores.confidence_score,
                    scores=scores,
                    warnings=self._warnings(context),
                    timestamp=datetime.now(timezone.utc),
                )
            )
        return tuple(results)

    def _warnings(self, ctx: EngineContextSnapshot) -> tuple[str, ...]:
        warnings: list[str] = []
        if ctx.critical_alert_count:
            warnings.append(f"{ctx.critical_alert_count} critical alerts active")
        if ctx.margin_utilization > Decimal("0.9"):
            warnings.append("Margin utilization above 90%")
        return tuple(warnings)
