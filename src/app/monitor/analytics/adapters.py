"""Engine output adapters for monitor summaries."""

from decimal import Decimal

from app.margin.models.result import MarginResult
from app.monitor.models.summaries import (
    GreeksSummary,
    MarginSummary,
    ProbabilitySummary,
    RiskSummary,
)
from app.probability.models.probability_result import ProbabilityResult
from app.risk.models.result import RiskResult


class GreeksAdapter:
    """Map risk engine greeks to monitor summary."""

    def from_risk(self, risk: RiskResult | None) -> GreeksSummary:
        """Build greeks summary without local calculation."""
        if risk is None:
            zero = Decimal("0")
            return GreeksSummary(zero, zero, zero, zero)
        return GreeksSummary(
            net_delta=risk.net_delta,
            net_gamma=risk.net_gamma,
            net_theta=risk.net_theta,
            net_vega=risk.net_vega,
        )


class RiskAdapter:
    """Map risk engine output to monitor summary."""

    def from_risk(self, risk: RiskResult | None) -> RiskSummary:
        """Build risk summary without local calculation."""
        if risk is None:
            zero = Decimal("0")
            return RiskSummary(zero, zero, zero, zero)
        return RiskSummary(
            value_at_risk=risk.value_at_risk,
            risk_score=risk.risk_score,
            capital_at_risk=risk.capital_at_risk,
            maximum_drawdown=risk.maximum_drawdown,
        )


class MarginAdapter:
    """Map margin engine output to monitor summary."""

    def from_margin(self, margin: MarginResult | None) -> MarginSummary:
        """Build margin summary without local calculation."""
        if margin is None:
            zero = Decimal("0")
            return MarginSummary(zero, zero, zero, zero)
        return MarginSummary(
            total_margin=margin.total_margin,
            available_margin=margin.available_margin,
            margin_utilization=margin.margin_utilization,
            buying_power=margin.buying_power,
        )


class ProbabilityAdapter:
    """Map probability engine output to monitor summary."""

    def from_probability(
        self,
        probability: ProbabilityResult | None,
    ) -> ProbabilitySummary:
        """Build probability summary without local calculation."""
        if probability is None:
            zero = Decimal("0")
            return ProbabilitySummary(zero, zero)
        return ProbabilitySummary(
            probability_of_profit=probability.probability_of_profit,
            expected_value=probability.expected_value,
        )
