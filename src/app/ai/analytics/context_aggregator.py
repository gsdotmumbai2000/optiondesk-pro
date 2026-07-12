"""Aggregate engine outputs into context snapshot."""

from decimal import Decimal

from app.ai.models.context import EngineContextSnapshot
from app.ai.models.request import RecommendationAnalysisRequest


class ContextAggregator:
    """Build context snapshot from engine outputs (no calculation)."""

    def aggregate(self, request: RecommendationAnalysisRequest) -> EngineContextSnapshot:
        """Aggregate metrics from frozen engine results."""
        portfolio = request.portfolio_result
        risk = request.risk_result
        margin = request.margin_result
        prob = request.probability_result
        monitor = request.position_monitor_result
        zero = Decimal("0")
        return EngineContextSnapshot(
            portfolio_value=portfolio.portfolio_value,
            unrealized_pnl=portfolio.unrealized_pnl,
            cash_balance=portfolio.cash_balance,
            net_delta=risk.net_delta if risk else portfolio.greeks_summary.net_delta,
            net_gamma=risk.net_gamma if risk else portfolio.greeks_summary.net_gamma,
            net_theta=risk.net_theta if risk else portfolio.greeks_summary.net_theta,
            net_vega=risk.net_vega if risk else portfolio.greeks_summary.net_vega,
            value_at_risk=risk.value_at_risk if risk else portfolio.risk_summary.value_at_risk,
            risk_score=risk.risk_score if risk else portfolio.risk_summary.risk_score,
            margin_utilization=margin.margin_utilization if margin else zero,
            available_margin=margin.available_margin if margin else portfolio.available_margin,
            probability_of_profit=(
                prob.probability_of_profit if prob else zero
            ),
            expected_value=prob.expected_value if prob else zero,
            health_score=monitor.health_score if monitor else Decimal("100"),
            open_position_count=len(portfolio.open_positions),
            critical_alert_count=len(monitor.critical_alerts) if monitor else 0,
        )
