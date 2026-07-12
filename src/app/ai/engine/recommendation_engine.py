"""AI recommendation engine entry point."""

from datetime import datetime, timezone

from app.ai.analytics.context_aggregator import ContextAggregator
from app.ai.models.batch import RecommendationBatchResult
from app.ai.models.request import RecommendationAnalysisRequest
from app.ai.models.result import RecommendationResult
from app.ai.models.rules import RecommendationRule
from app.ai.recommendations.generator import RecommendationGenerator
from app.ai.rules.rule_engine import RecommendationRuleEngine
from app.ai.rules.rule_registry import RuleRegistry


class RecommendationEngine:
    """Enterprise AI recommendation engine."""

    def __init__(self) -> None:
        """Initialize engine components."""
        self._aggregator = ContextAggregator()
        self._registry = RuleRegistry()
        self._rules = RecommendationRuleEngine()
        self._generator = RecommendationGenerator()

    def generate(
        self,
        request: RecommendationAnalysisRequest,
        custom_rules: tuple[RecommendationRule, ...] = (),
    ) -> RecommendationBatchResult:
        """Generate recommendations from engine outputs."""
        context = self._aggregator.aggregate(request)
        rules = self._registry.enabled_rules(custom_rules)
        matched = self._rules.evaluate(request, context, rules)
        recommendations = self._generator.generate(request, context, matched)
        primary = self._select_primary(recommendations)
        return RecommendationBatchResult(
            recommendations=recommendations,
            primary=primary,
            calculation_timestamp=datetime.now(timezone.utc),
        )

    def _select_primary(
        self,
        recommendations: tuple[RecommendationResult, ...],
    ) -> RecommendationResult | None:
        if not recommendations:
            return None
        return max(recommendations, key=lambda r: r.scores.priority_score)
