"""Tests for real notification delivery: NotificationService.send() (build +
deliver through a configured NotificationChannel) and AlertService wiring
notifications into raise_alerts(). Previously NotificationService only ever
built AlertNotification payloads -- nothing sent them anywhere.
"""

from datetime import datetime, timezone
from decimal import Decimal

from app.monitor.models.alert import Alert
from app.monitor.models.enums import AlertPriority, AlertStatus, TriggerType
from app.monitor.services.alert_service import AlertService
from app.monitor.services.notification_service import NotificationService


def _alert(priority: AlertPriority = AlertPriority.WARNING) -> Alert:
    return Alert(
        alert_id="A1", rule_id="R1", trigger_type=TriggerType.LOSS_THRESHOLD,
        priority=priority, status=AlertStatus.OPEN, title="Max loss breached",
        message="Position loss exceeded threshold", symbol="NIFTY",
        observed_value=Decimal("-5000"), threshold=Decimal("-4000"),
        raised_at=datetime.now(timezone.utc),
    )


class _RecordingChannel:
    def __init__(self, result: bool = True, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.received: list = []

    def send(self, notification) -> bool:
        self.received.append(notification)
        if self.error is not None:
            raise self.error
        return self.result


class TestNotificationServiceSend:
    def test_no_channel_configured_still_returns_built_notification(self) -> None:
        service = NotificationService()
        notification = service.send(_alert())

        assert notification.subject == "Max loss breached"
        assert notification.body == "Position loss exceeded threshold"

    def test_configured_channel_receives_the_notification(self) -> None:
        channel = _RecordingChannel()
        service = NotificationService(channel)

        notification = service.send(_alert())

        assert channel.received == [notification]

    def test_channel_returning_false_does_not_raise(self) -> None:
        service = NotificationService(_RecordingChannel(result=False))

        notification = service.send(_alert())  # must not raise

        assert notification is not None

    def test_channel_raising_does_not_propagate(self) -> None:
        service = NotificationService(_RecordingChannel(error=RuntimeError("tray unavailable")))

        notification = service.send(_alert())  # must not raise

        assert notification is not None

    def test_priority_carried_into_notification_metadata(self) -> None:
        service = NotificationService()

        notification = service.send(_alert(AlertPriority.CRITICAL))

        assert notification.metadata["priority"] == "CRITICAL"

    def test_set_channel_late_binds_delivery(self) -> None:
        service = NotificationService()  # no channel yet
        channel = _RecordingChannel()

        service.set_channel(channel)
        service.send(_alert())

        assert len(channel.received) == 1

    def test_set_channel_none_clears_delivery(self) -> None:
        channel = _RecordingChannel()
        service = NotificationService(channel)

        service.set_channel(None)
        service.send(_alert())

        assert channel.received == []  # never reached after clearing


class TestAlertServiceDeliversNotifications:
    def test_raise_alerts_sends_through_configured_notification_service(self) -> None:
        channel = _RecordingChannel()
        notifications = NotificationService(channel)
        service = AlertService(notification_service=notifications)

        service.raise_alerts((_alert(),))

        assert len(channel.received) == 1
        assert channel.received[0].alert_id == "A1"

    def test_multiple_alerts_each_get_a_notification(self) -> None:
        channel = _RecordingChannel()
        notifications = NotificationService(channel)
        service = AlertService(notification_service=notifications)

        service.raise_alerts((_alert(), _alert(), _alert()))

        assert len(channel.received) == 3

    def test_no_notification_service_configured_does_not_crash(self) -> None:
        service = AlertService()  # notification_service defaults to None

        service.raise_alerts((_alert(),))  # must not raise

        assert len(service.open_alerts()) == 1

    def test_alerts_still_registered_in_manager_regardless_of_delivery(self) -> None:
        channel = _RecordingChannel(error=RuntimeError("boom"))
        notifications = NotificationService(channel)
        service = AlertService(notification_service=notifications)

        service.raise_alerts((_alert(),))

        assert len(service.open_alerts()) == 1  # delivery failure doesn't block registration
