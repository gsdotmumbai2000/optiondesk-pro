"""Engine analysis context snapshot."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class EngineContextSnapshot:
    """Aggregated engine metrics for advisors (no calculation)."""

    portfolio_value: Decimal
    unrealized_pnl: Decimal
    cash_balance: Decimal
    net_delta: Decimal
    net_gamma: Decimal
    net_theta: Decimal
    net_vega: Decimal
    value_at_risk: Decimal
    risk_score: Decimal
    margin_utilization: Decimal
    available_margin: Decimal
    probability_of_profit: Decimal
    expected_value: Decimal
    health_score: Decimal
    open_position_count: int
    critical_alert_count: int
