"""Notification service (framework for future channels)."""

from datetime import datetime, timezone

from app.monitor.models.alert import Alert, AlertNotification
from app.utils.uuid_helper import generate_uuid


class NotificationService:
    """Build notification payloads (no delivery implementation)."""

    def build(self, alert: Alert, channel: str = "in_app") -> AlertNotification:
        """Create notification payload for alert."""
        return AlertNotification(
            notification_id=generate_uuid(),
            alert_id=alert.alert_id,
            channel=channel,
            recipient="",
            subject=alert.title,
            body=alert.message,
            created_at=datetime.now(timezone.utc),
            metadata={"priority": alert.priority.value},
        )

    def build_batch(
        self,
        alerts: tuple[Alert, ...],
        channel: str = "in_app",
    ) -> tuple[AlertNotification, ...]:
        """Build notifications for multiple alerts."""
        return tuple(self.build(alert, channel) for alert in alerts)
