"""Alert application service."""

from app.events.event_bus import EventBus
from app.monitor.alerts.manager import AlertManager
from app.monitor.events import AlertAcknowledgedEvent, AlertRaisedEvent
from app.monitor.models.alert import Alert


class AlertService:
    """Manage alerts and acknowledgements."""

    def __init__(
        self,
        manager: AlertManager | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize service."""
        self._manager = manager or AlertManager()
        self._event_bus = event_bus

    @property
    def manager(self) -> AlertManager:
        """Return alert manager."""
        return self._manager

    def raise_alerts(self, alerts: tuple[Alert, ...]) -> None:
        """Register alerts and publish events."""
        for alert in alerts:
            self._manager.add(alert)
            self._publish_raised(alert)

    def acknowledge(self, alert_id: str) -> Alert | None:
        """Acknowledge alert."""
        ack = self._manager.acknowledge(alert_id)
        if ack is not None:
            self._publish_acknowledged(ack)
        return ack

    def open_alerts(self) -> tuple[Alert, ...]:
        """Return open alerts."""
        return self._manager.open_alerts

    def _publish_raised(self, alert: Alert) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            AlertRaisedEvent(payload={"alert_id": alert.alert_id})
        )

    def _publish_acknowledged(self, alert: Alert) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            AlertAcknowledgedEvent(payload={"alert_id": alert.alert_id})
        )
