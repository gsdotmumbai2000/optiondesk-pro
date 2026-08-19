"""Tests for DesktopToastChannel: NotificationChannel implementation
backed by QSystemTrayIcon, wired into MainWindow as the real alert-delivery
channel."""

from datetime import datetime, timezone

import pytest
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from app.monitor.models.alert import AlertNotification
from app.ui.notifications.desktop_toast_channel import DesktopToastChannel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _notification(priority: str = "WARNING") -> AlertNotification:
    return AlertNotification(
        notification_id="N1", alert_id="A1", channel="desktop", recipient="",
        subject="Max loss breached", body="Position loss exceeded threshold",
        created_at=datetime.now(timezone.utc), metadata={"priority": priority},
    )


class _FakeTrayIcon:
    """QSystemTrayIcon double: avoids depending on a real system tray being
    available in the test environment (CI, headless runners)."""

    def __init__(self, *, visible: bool = True, raise_on_show: Exception | None = None) -> None:
        self._visible = visible
        self._raise_on_show = raise_on_show
        self.shown: list[tuple] = []

    def isVisible(self) -> bool:
        return self._visible

    def showMessage(self, title, body, icon, timeout) -> None:
        if self._raise_on_show is not None:
            raise self._raise_on_show
        self.shown.append((title, body, icon, timeout))


class TestDesktopToastChannelSuccess:
    def test_visible_tray_delivers_and_returns_true(self, qapp: QApplication) -> None:
        tray = _FakeTrayIcon(visible=True)
        channel = DesktopToastChannel(tray)

        result = channel.send(_notification())

        assert result is True
        assert len(tray.shown) == 1

    def test_subject_and_body_passed_through_unchanged(self, qapp: QApplication) -> None:
        tray = _FakeTrayIcon()
        channel = DesktopToastChannel(tray)

        channel.send(_notification())

        title, body, _, _ = tray.shown[0]
        assert title == "Max loss breached"
        assert body == "Position loss exceeded threshold"

    def test_critical_priority_maps_to_critical_icon(self, qapp: QApplication) -> None:
        tray = _FakeTrayIcon()
        channel = DesktopToastChannel(tray)

        channel.send(_notification(priority="CRITICAL"))

        _, _, icon, _ = tray.shown[0]
        assert icon == QSystemTrayIcon.MessageIcon.Critical

    def test_unknown_priority_falls_back_to_information_icon(self, qapp: QApplication) -> None:
        tray = _FakeTrayIcon()
        channel = DesktopToastChannel(tray)

        channel.send(_notification(priority="SOMETHING_UNKNOWN"))

        _, _, icon, _ = tray.shown[0]
        assert icon == QSystemTrayIcon.MessageIcon.Information


class TestDesktopToastChannelUnavailable:
    def test_tray_not_visible_returns_false_without_calling_show_message(self, qapp: QApplication) -> None:
        tray = _FakeTrayIcon(visible=False)
        channel = DesktopToastChannel(tray)

        result = channel.send(_notification())

        assert result is False
        assert tray.shown == []

    def test_show_message_raising_returns_false_not_raises(self, qapp: QApplication) -> None:
        tray = _FakeTrayIcon(raise_on_show=RuntimeError("OS toast failed"))
        channel = DesktopToastChannel(tray)

        result = channel.send(_notification())  # must not raise

        assert result is False
