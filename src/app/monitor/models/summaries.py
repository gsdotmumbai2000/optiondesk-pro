"""Engine summary adapters for monitor output."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class GreeksSummary:
    """Greeks from risk engine (no local calculation)."""

    net_delta: Decimal
    net_gamma: Decimal
    net_theta: Decimal
    net_vega: Decimal


@dataclass(frozen=True, slots=True)
class RiskSummary:
    """Risk from risk engine."""

    value_at_risk: Decimal
    risk_score: Decimal
    capital_at_risk: Decimal
    maximum_drawdown: Decimal


@dataclass(frozen=True, slots=True)
class MarginSummary:
    """Margin from margin engine."""

    total_margin: Decimal
    available_margin: Decimal
    margin_utilization: Decimal
    buying_power: Decimal


@dataclass(frozen=True, slots=True)
class ProbabilitySummary:
    """Probability from probability engine."""

    probability_of_profit: Decimal
    expected_value: Decimal
