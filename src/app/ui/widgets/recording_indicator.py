"""NIFTY tick recording indicator for status bar."""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class RecordingIndicator(QWidget):
    """Small badge shown only while NIFTY tick recording is active."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize indicator, hidden until recording starts."""
        super().__init__(parent)
        self._dot = QLabel("●")
        self._dot.setStyleSheet("color: #e74c3c; font-size: 14px;")
        self._label = QLabel("Recording")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.addWidget(self._dot)
        layout.addWidget(self._label)
        self.hide()

    def set_recording(self, active: bool, tick_count: int = 0) -> None:
        """Show/update the badge while recording, hide it otherwise."""
        if not active:
            self.hide()
            return
        self._label.setText(f"Recording ({tick_count} ticks)" if tick_count else "Recording")
        self.show()
