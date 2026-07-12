"""Alert domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.monitor.models.enums import AlertPriority, AlertStatus, RuleType, TriggerType


@dataclass(frozen=True, slots=True)
class AlertRule:
    """Configurable alert rule."""

    rule_id: str
    rule_type: RuleType
    name: str
    threshold: Decimal
    enabled: bool = True
    priority: AlertPriority = AlertPriority.WARNING
    symbol: str = ""
    custom_expression: str = ""


@dataclass(frozen=True, slots=True)
class AlertTrigger:
    """Fired trigger before alert materialization."""

    trigger_id: str
    trigger_type: TriggerType
    rule_id: str
    symbol: str
    observed_value: Decimal
    threshold: Decimal
    triggered_at: datetime


@dataclass(frozen=True, slots=True)
class Alert:
    """Immutable alert record."""

    alert_id: str
    rule_id: str
    trigger_type: TriggerType
    priority: AlertPriority
    status: AlertStatus
    title: str
    message: str
    symbol: str
    observed_value: Decimal
    threshold: Decimal
    raised_at: datetime
    acknowledged_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class AlertNotification:
    """Notification payload for an alert (framework)."""

    notification_id: str
    alert_id: str
    channel: str
    recipient: str
    subject: str
    body: str
    created_at: datetime
    metadata: dict[str, str] = field(default_factory=dict)
