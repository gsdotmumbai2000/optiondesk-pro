"""Tests for the recording status bar indicator."""

import pytest
from PySide6.QtWidgets import QApplication

from app.ui.widgets.recording_indicator import RecordingIndicator


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Provide a Qt application instance for widget tests."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_hidden_by_default(qapp: QApplication) -> None:
    """Badge should start hidden until recording is active."""
    indicator = RecordingIndicator()
    assert not indicator.isVisible()


def test_shows_with_tick_count(qapp: QApplication) -> None:
    """Badge should become visible and show the running tick count."""
    indicator = RecordingIndicator()
    indicator.show()
    indicator.set_recording(True, 42)
    assert indicator.isVisible()
    assert "42" in indicator._label.text()


def test_shows_without_tick_count(qapp: QApplication) -> None:
    """Badge should show a plain label when no count is given yet."""
    indicator = RecordingIndicator()
    indicator.show()
    indicator.set_recording(True)
    assert indicator._label.text() == "Recording"


def test_hides_when_inactive(qapp: QApplication) -> None:
    """Badge should hide again once recording is inactive."""
    indicator = RecordingIndicator()
    indicator.show()
    indicator.set_recording(True, 5)
    indicator.set_recording(False)
    assert not indicator.isVisible()
