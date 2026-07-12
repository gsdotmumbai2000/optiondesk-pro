"""Market status indicator for status bar."""

from PySide6.QtWidgets import QLabel, QWidget


class MarketStatusIndicator(QWidget):
    """Compact market status and last tick time."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize indicator."""
        super().__init__(parent)
        from PySide6.QtWidgets import QHBoxLayout

        self._label = QLabel("Market: — | Last tick: —")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.addWidget(self._label)

    def update_status(self, market_status: str, last_tick: str, connected: str) -> None:
        """Update status bar text."""
        self._label.setText(
            f"Market: {market_status} | Broker: {connected} | Last tick: {last_tick}"
        )
