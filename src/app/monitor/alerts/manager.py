"""Alert factory and manager."""

from dataclasses import replace
from datetime import datetime, timezone

from app.monitor.models.alert import Alert, AlertRule, AlertTrigger
from app.monitor.models.enums import AlertPriority, AlertStatus
from app.utils.uuid_helper import generate_uuid


class AlertFactory:
    """Materialize alerts from triggers."""

    def create(self, trigger: AlertTrigger, rule: AlertRule) -> Alert:
        """Create alert from trigger and rule."""
        title = f"{rule.name} triggered"
        message = (
            f"{rule.name}: observed {trigger.observed_value} "
            f"threshold {trigger.threshold}"
        )
        return Alert(
            alert_id=generate_uuid(),
            rule_id=rule.rule_id,
            trigger_type=trigger.trigger_type,
            priority=rule.priority,
            status=AlertStatus.OPEN,
            title=title,
            message=message,
            symbol=trigger.symbol,
            observed_value=trigger.observed_value,
            threshold=trigger.threshold,
            raised_at=trigger.triggered_at,
        )


class AlertManager:
    """Manage open and acknowledged alerts."""

    def __init__(self) -> None:
        """Initialize manager."""
        self._open: list[Alert] = []
        self._acknowledged: list[Alert] = []

    @property
    def open_alerts(self) -> tuple[Alert, ...]:
        """Return open alerts."""
        return tuple(self._open)

    @property
    def acknowledged_alerts(self) -> tuple[Alert, ...]:
        """Return acknowledged alerts."""
        return tuple(self._acknowledged)

    def add(self, alert: Alert) -> None:
        """Add new alert."""
        self._open.append(alert)

    def acknowledge(self, alert_id: str) -> Alert | None:
        """Acknowledge alert by id."""
        for idx, alert in enumerate(self._open):
            if alert.alert_id == alert_id:
                ack = replace(
                    alert,
                    status=AlertStatus.ACKNOWLEDGED,
                    acknowledged_at=datetime.now(timezone.utc),
                )
                self._open.pop(idx)
                self._acknowledged.append(ack)
                return ack
        return None

    def filter_by_priority(
        self,
        priority: AlertPriority,
    ) -> tuple[Alert, ...]:
        """Return open alerts matching priority."""
        return tuple(a for a in self._open if a.priority == priority)

    def map_rules(
        self,
        triggers: tuple[AlertTrigger, ...],
        rules: tuple[AlertRule, ...],
    ) -> dict[str, AlertRule]:
        """Build rule lookup."""
        return {r.rule_id: r for r in rules}

    def from_triggers(
        self,
        triggers: tuple[AlertTrigger, ...],
        rules: tuple[AlertRule, ...],
        factory: AlertFactory | None = None,
    ) -> tuple[Alert, ...]:
        """Create alerts from triggers."""
        lookup = self.map_rules(triggers, rules)
        creator = factory or AlertFactory()
        alerts: list[Alert] = []
        for trigger in triggers:
            rule = lookup.get(trigger.rule_id)
            if rule is None:
                continue
            alerts.append(creator.create(trigger, rule))
        return tuple(alerts)
