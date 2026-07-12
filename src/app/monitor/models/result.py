"""Monitor analysis result."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.monitor.models.alert import Alert
from app.monitor.models.enums import MonitorModelVersion, PositionHealth
from app.monitor.models.monitor import PositionSnapshot
from app.monitor.models.recommendation import Recommendation
from app.monitor.models.summaries import (
    GreeksSummary,
    MarginSummary,
    ProbabilitySummary,
    RiskSummary,
)


@dataclass(frozen=True, slots=True)
class MonitorResult:
    """Immutable monitor analytics output."""

    position_status: PositionHealth
    open_alerts: tuple[Alert, ...]
    critical_alerts: tuple[Alert, ...]
    warning_alerts: tuple[Alert, ...]
    adjustment_suggestions: tuple[Recommendation, ...]
    exit_suggestions: tuple[Recommendation, ...]
    risk_summary: RiskSummary
    margin_summary: MarginSummary
    greeks_summary: GreeksSummary
    probability_summary: ProbabilitySummary
    health_score: Decimal
    recommendation_list: tuple[Recommendation, ...]
    position_snapshots: tuple[PositionSnapshot, ...]
    calculation_timestamp: datetime
    model_version: MonitorModelVersion = MonitorModelVersion.V1
