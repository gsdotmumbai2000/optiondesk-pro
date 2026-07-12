"""Monitor engine entry point."""

from datetime import datetime, timezone

from app.monitor.alerts.manager import AlertManager
from app.monitor.analytics.adapters import (
    GreeksAdapter,
    MarginAdapter,
    ProbabilityAdapter,
    RiskAdapter,
)
from app.monitor.analytics.health_scorer import HealthScorer
from app.monitor.analytics.position_analyzer import PositionAnalyzer
from app.monitor.models.enums import AlertPriority
from app.monitor.models.request import MonitorAnalysisRequest
from app.monitor.models.result import MonitorResult
from app.monitor.recommendations.engine import RecommendationEngine
from app.monitor.rules.rule_registry import RuleRegistry
from app.monitor.triggers.evaluator import TriggerEvaluator


class MonitorEngine:
    """Enterprise position monitor and alert engine."""

    def __init__(self) -> None:
        """Initialize engine components."""
        self._registry = RuleRegistry()
        self._triggers = TriggerEvaluator()
        self._alerts = AlertManager()
        self._recommendations = RecommendationEngine()
        self._positions = PositionAnalyzer()
        self._health = HealthScorer()
        self._greeks = GreeksAdapter()
        self._risk = RiskAdapter()
        self._margin = MarginAdapter()
        self._probability = ProbabilityAdapter()

    def evaluate(self, request: MonitorAnalysisRequest) -> MonitorResult:
        """Evaluate positions and generate monitor result."""
        rules = self._registry.enabled_rules(request.rules)
        fired = self._triggers.evaluate(request, rules)
        alerts = self._alerts.from_triggers(fired, rules)
        for alert in alerts:
            self._alerts.add(alert)
        snapshots = self._positions.snapshots(
            request.portfolio_result.open_positions,
            alerts,
        )
        status = self._positions.aggregate_health(alerts, snapshots)
        recs = self._recommendations.generate(request, alerts)
        return MonitorResult(
            position_status=status,
            open_alerts=alerts,
            critical_alerts=self._filter_priority(alerts, AlertPriority.CRITICAL),
            warning_alerts=self._filter_priority(alerts, AlertPriority.WARNING),
            adjustment_suggestions=self._recommendations.adjustments(recs),
            exit_suggestions=self._recommendations.exits(recs),
            risk_summary=self._risk.from_risk(request.risk_result),
            margin_summary=self._margin.from_margin(request.margin_result),
            greeks_summary=self._greeks.from_risk(request.risk_result),
            probability_summary=self._probability.from_probability(
                request.probability_result
            ),
            health_score=self._health.score(alerts, status),
            recommendation_list=recs,
            position_snapshots=snapshots,
            calculation_timestamp=datetime.now(timezone.utc),
        )

    def _filter_priority(self, alerts, priority: AlertPriority):
        return tuple(a for a in alerts if a.priority == priority)
