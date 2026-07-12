"""Supporting evidence builder from engine outputs."""

from app.ai.models.context import EngineContextSnapshot
from app.ai.models.enums import EvidenceSource
from app.ai.models.evidence import EvidenceMetric, SupportingEvidence
from app.ai.models.request import RecommendationAnalysisRequest
from app.ai.models.rules import RecommendationRule
from app.utils.uuid_helper import generate_uuid


class EvidenceBuilder:
    """Build traceable evidence from engine outputs."""

    def build(
        self,
        request: RecommendationAnalysisRequest,
        context: EngineContextSnapshot,
        rule: RecommendationRule,
    ) -> SupportingEvidence:
        """Create supporting evidence for a recommendation."""
        metrics = self._collect_metrics(request, context)
        affected = self._affected_for_rule(rule)
        return SupportingEvidence(
            evidence_id=generate_uuid(),
            summary=f"Rule {rule.condition.value} triggered at threshold {rule.threshold}",
            metrics=metrics,
            affected_metrics=affected,
        )

    def _collect_metrics(
        self,
        request: RecommendationAnalysisRequest,
        ctx: EngineContextSnapshot,
    ) -> tuple[EvidenceMetric, ...]:
        metrics: list[EvidenceMetric] = [
            self._metric(EvidenceSource.PORTFOLIO, "unrealized_pnl", ctx.unrealized_pnl),
            self._metric(EvidenceSource.PORTFOLIO, "portfolio_value", ctx.portfolio_value),
            self._metric(EvidenceSource.RISK, "net_delta", ctx.net_delta),
            self._metric(EvidenceSource.RISK, "risk_score", ctx.risk_score),
            self._metric(EvidenceSource.MARGIN, "margin_utilization", ctx.margin_utilization),
            self._metric(EvidenceSource.PROBABILITY, "probability_of_profit", ctx.probability_of_profit),
        ]
        if request.position_monitor_result:
            metrics.append(
                self._metric(
                    EvidenceSource.MONITOR,
                    "health_score",
                    request.position_monitor_result.health_score,
                )
            )
        return tuple(metrics)

    def _metric(self, source: EvidenceSource, name: str, value) -> EvidenceMetric:
        return EvidenceMetric(
            source=source,
            metric_name=name,
            metric_value=str(value),
            engine_reference=f"{source.value}.{name}",
        )

    def _affected_for_rule(self, rule: RecommendationRule) -> tuple[str, ...]:
        from app.ai.models.enums import RuleCondition

        mapping = {
            RuleCondition.DELTA_EXCEEDS: ("net_delta", "directional_exposure"),
            RuleCondition.MARGIN_UTILIZATION_EXCEEDS: (
                "margin_utilization",
                "available_margin",
            ),
            RuleCondition.POP_BELOW: ("probability_of_profit", "expected_value"),
            RuleCondition.RISK_SCORE_EXCEEDS: ("risk_score", "value_at_risk"),
            RuleCondition.LOSS_EXCEEDS: ("unrealized_pnl",),
            RuleCondition.HEALTH_SCORE_BELOW: ("health_score",),
        }
        return mapping.get(rule.condition, ("portfolio_value",))
