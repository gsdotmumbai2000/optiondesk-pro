"""Notification delivery channel port."""

from typing import Protocol

from app.monitor.models.alert import AlertNotification


class NotificationChannel(Protocol):
    """Deliver a built notification payload somewhere real (desktop toast,
    email, webhook, ...). Implementations live outside the monitor module
    (e.g. the UI layer for a desktop toast) since delivery mechanisms are
    infrastructure, not domain logic."""

    def send(self, notification: AlertNotification) -> bool:
        """Attempt delivery. Return True on success, False on failure --
        implementations should catch their own delivery errors rather than
        raising, so one bad notification never breaks alert raising."""
