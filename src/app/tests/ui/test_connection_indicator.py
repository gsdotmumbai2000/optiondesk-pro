"""Tests for connection indicator status normalization."""

import pytest
from PySide6.QtWidgets import QApplication

from app.brokers.shared.enums import BrokerConnectionStatus
from app.ui.widgets.connection_indicator import (
    ConnectionIndicator,
    connection_status_label,
    normalize_connection_status,
)


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Provide a Qt application instance for widget tests."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class TestNormalizeConnectionStatus:
    """normalize_connection_status accepts enum and string inputs."""

    def test_accepts_enum(self) -> None:
        assert (
            normalize_connection_status(BrokerConnectionStatus.CONNECTED)
            == BrokerConnectionStatus.CONNECTED
        )

    def test_accepts_display_value_string(self) -> None:
        assert (
            normalize_connection_status("Connected")
            == BrokerConnectionStatus.CONNECTED
        )

    def test_accepts_enum_name_string(self) -> None:
        assert (
            normalize_connection_status("AUTHENTICATION_FAILED")
            == BrokerConnectionStatus.AUTHENTICATION_FAILED
        )

    def test_accepts_spaced_label_string(self) -> None:
        assert (
            normalize_connection_status("Authentication Failed")
            == BrokerConnectionStatus.AUTHENTICATION_FAILED
        )

    def test_unknown_string_defaults_to_disconnected(self) -> None:
        assert (
            normalize_connection_status("Unknown")
            == BrokerConnectionStatus.DISCONNECTED
        )


class TestConnectionStatusLabel:
    """connection_status_label never requires .value on strings."""

    def test_enum_returns_value(self) -> None:
        assert connection_status_label(BrokerConnectionStatus.EXPIRED) == "Expired"

    def test_string_returns_as_is(self) -> None:
        assert connection_status_label("Custom Status") == "Custom Status"

    def test_empty_string_defaults_to_disconnected_label(self) -> None:
        assert connection_status_label("") == BrokerConnectionStatus.DISCONNECTED.value


class TestConnectionIndicator:
    """Widget methods accept enum and string status values."""

    def test_update_status_with_string_does_not_raise(
        self, qapp: QApplication
    ) -> None:
        indicator = ConnectionIndicator()
        indicator.update_status("ICICI Breeze", "Connected", "user1", "production")
        assert "Connected" in indicator._label.text()

    def test_update_status_with_enum(self, qapp: QApplication) -> None:
        indicator = ConnectionIndicator()
        indicator.update_status(
            "ICICI Breeze",
            BrokerConnectionStatus.CONNECTING,
            "user1",
            "sandbox",
        )
        assert "Connecting" in indicator._label.text()

    def test_set_color_with_string(self, qapp: QApplication) -> None:
        indicator = ConnectionIndicator()
        indicator.set_color("Authentication Failed")
        assert "#e74c3c" in indicator._dot.styleSheet()

    def test_set_color_with_enum(self, qapp: QApplication) -> None:
        indicator = ConnectionIndicator()
        indicator.set_color(BrokerConnectionStatus.RECONNECT_REQUIRED)
        assert "#e67e22" in indicator._dot.styleSheet()
