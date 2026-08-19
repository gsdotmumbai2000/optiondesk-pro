"""Real notification delivery via the OS-native desktop tray toast --
implements app.monitor.services.notification_channel.NotificationChannel.
No external service or credentials needed (unlike email/SMS/webhook
channels), since it uses QSystemTrayIcon, already available through the
PySide6 dependency this app already has."""

from PySide6.QtWidgets import QSystemTrayIcon

from app.logging.logging_manager import get_logger
from app.monitor.models.alert import AlertNotification

logger = get_logger(__name__)

_PRIORITY_ICONS = {
    "INFORMATION": QSystemTrayIcon.MessageIcon.Information,
    "WARNING": QSystemTrayIcon.MessageIcon.Warning,
    "CRITICAL": QSystemTrayIcon.MessageIcon.Critical,
    "EMERGENCY": QSystemTrayIcon.MessageIcon.Critical,
}
_TOAST_TIMEOUT_MS = 8000


class DesktopToastChannel:
    """NotificationChannel backed by a QSystemTrayIcon."""

    def __init__(self, tray_icon: QSystemTrayIcon) -> None:
        self._tray_icon = tray_icon

    def send(self, notification: AlertNotification) -> bool:
        """Show a desktop toast for `notification`. Returns False (without
        raising) when the tray icon isn't actually visible -- e.g. no
        system tray is available on this machine/session -- so callers
        treat it the same as any other unavailable channel."""
        if not self._tray_icon.isVisible():
            return False
        icon = _PRIORITY_ICONS.get(
            notification.metadata.get("priority", ""), QSystemTrayIcon.MessageIcon.Information,
        )
        try:
            self._tray_icon.showMessage(notification.subject, notification.body, icon, _TOAST_TIMEOUT_MS)
        except Exception as error:  # noqa: BLE001 - OS-level call, must never crash the caller
            logger.warning("Desktop toast delivery failed: {error}", error=error)
            return False
        return True
