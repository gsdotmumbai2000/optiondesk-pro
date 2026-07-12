"""Recommendation engine (framework only, no AI)."""

from datetime import datetime, timezone
from decimal import Decimal

from app.monitor.models.alert import Alert
from app.monitor.models.enums import AlertPriority, RecommendationType, TriggerType
from app.monitor.models.recommendation import Recommendation
from app.monitor.models.request import MonitorAnalysisRequest
from app.utils.uuid_helper import generate_uuid


class RecommendationEngine:
    """Generate framework recommendations from alerts and engine data."""

    def generate(
        self,
        request: MonitorAnalysisRequest,
        alerts: tuple[Alert, ...],
    ) -> tuple[Recommendation, ...]:
        """Build recommendations from fired alerts."""
        recs: list[Recommendation] = []
        for alert in alerts:
            rec = self._from_alert(alert, request)
            if rec is not None:
                recs.append(rec)
        recs.extend(self._margin_recommendations(request))
        return tuple(recs)

    def adjustments(
        self,
        recommendations: tuple[Recommendation, ...],
    ) -> tuple[Recommendation, ...]:
        """Filter adjustment suggestions."""
        types = {
            RecommendationType.REDUCE_POSITION,
            RecommendationType.HEDGE_POSITION,
            RecommendationType.REDUCE_RISK,
            RecommendationType.INCREASE_CAPITAL,
            RecommendationType.ROLL_POSITION,
        }
        return tuple(r for r in recommendations if r.recommendation_type in types)

    def exits(
        self,
        recommendations: tuple[Recommendation, ...],
    ) -> tuple[Recommendation, ...]:
        """Filter exit suggestions."""
        types = {
            RecommendationType.CLOSE_POSITION,
            RecommendationType.TAKE_PROFIT,
        }
        return tuple(r for r in recommendations if r.recommendation_type in types)

    def _from_alert(
        self,
        alert: Alert,
        request: MonitorAnalysisRequest,
    ) -> Recommendation | None:
        mapping = {
            TriggerType.LOSS_THRESHOLD: (
                RecommendationType.REDUCE_RISK,
                "Reduce risk exposure",
            ),
            TriggerType.PROFIT_TARGET: (
                RecommendationType.TAKE_PROFIT,
                "Consider taking profit",
            ),
            TriggerType.MARGIN_LIMIT: (
                RecommendationType.INCREASE_CAPITAL,
                "Increase capital or reduce positions",
            ),
            TriggerType.DELTA_LIMIT: (
                RecommendationType.HEDGE_POSITION,
                "Hedge delta exposure",
            ),
            TriggerType.GAMMA_LIMIT: (
                RecommendationType.REDUCE_POSITION,
                "Reduce gamma exposure",
            ),
            TriggerType.THETA_DECAY: (
                RecommendationType.ROLL_POSITION,
                "Consider rolling before theta decay",
            ),
            TriggerType.EXPIRY_WARNING: (
                RecommendationType.CLOSE_POSITION,
                "Close or roll before expiry",
            ),
            TriggerType.VOLATILITY_SPIKE: (
                RecommendationType.REDUCE_POSITION,
                "Reduce vega exposure",
            ),
        }
        entry = mapping.get(alert.trigger_type)
        if entry is None:
            return None
        rec_type, action = entry
        return Recommendation(
            recommendation_id=generate_uuid(),
            recommendation_type=rec_type,
            symbol=alert.symbol,
            title=alert.title,
            rationale=alert.message,
            priority=alert.priority,
            suggested_action=action,
            confidence=Decimal("0.75"),
            generated_at=datetime.now(timezone.utc),
        )

    def _margin_recommendations(
        self,
        request: MonitorAnalysisRequest,
    ) -> list[Recommendation]:
        margin = request.margin_result
        if margin is None or margin.margin_utilization < Decimal("0.9"):
            return []
        return [
            Recommendation(
                recommendation_id=generate_uuid(),
                recommendation_type=RecommendationType.REDUCE_RISK,
                symbol="",
                title="High margin utilization",
                rationale="Margin utilization exceeds 90%",
                priority=AlertPriority.CRITICAL,
                suggested_action="Reduce positions or add capital",
                confidence=Decimal("0.85"),
                generated_at=datetime.now(timezone.utc),
            )
        ]
