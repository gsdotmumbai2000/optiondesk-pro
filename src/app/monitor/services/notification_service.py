"""Notification service: builds notification payloads and, once a real
NotificationChannel is configured (e.g. a desktop toast channel wired in by
the UI layer at startup), actually delivers them."""

from datetime import datetime, timezone

from app.logging.logging_manager import get_logger
from app.monitor.models.alert import Alert, AlertNotification
from app.monitor.services.notification_channel import NotificationChannel
from app.utils.uuid_helper import generate_uuid

logger = get_logger(__name__)


class NotificationService:
    """Build and, when a channel is configured, deliver notifications."""

    def __init__(self, channel: NotificationChannel | None = None) -> None:
        """Initialize service. `channel` is optional so this stays usable
        (build-only, matching prior behavior) before a real channel is
        wired in -- e.g. during headless/test construction."""
        self._channel = channel

    def set_channel(self, channel: NotificationChannel | None) -> None:
        """Configure (or clear) the delivery channel. Late-bindable since
        the real channel (e.g. a desktop toast icon) is usually only
        constructible once the UI layer exists, after this service does."""
        self._channel = channel

    def build(self, alert: Alert, channel: str = "in_app", recipient: str = "") -> AlertNotification:
        """Create notification payload for alert."""
        return AlertNotification(
            notification_id=generate_uuid(),
            alert_id=alert.alert_id,
            channel=channel,
            recipient=recipient,
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

    def send(self, alert: Alert, channel: str = "in_app", recipient: str = "") -> AlertNotification:
        """Build a notification and deliver it through the configured
        channel. Always returns the built notification, even when no
        channel is configured or delivery fails -- delivery is best-effort
        and logged, never raised, so one bad notification can't break
        alert raising."""
        notification = self.build(alert, channel, recipient)
        if self._channel is None:
            return notification
        try:
            delivered = self._channel.send(notification)
        except Exception as error:  # noqa: BLE001 - delivery must never crash the caller
            logger.warning(
                "Notification delivery raised for alert {alert_id}: {error}",
                alert_id=alert.alert_id,
                error=error,
            )
            return notification
        if not delivered:
            logger.warning("Notification delivery failed for alert {alert_id}", alert_id=alert.alert_id)
        return notification
