"""Reusable live price display widget."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from app.utils.datetime_helper import DateTimeHelper


class LivePriceWidget(QWidget):
    """Display live spot price, change, and last update time."""

    def __init__(self, title: str = "Live Price", parent: QWidget | None = None) -> None:
        """Initialize widget."""
        super().__init__(parent)
        self._title = QLabel(title)
        self._title.setStyleSheet("font-weight: bold;")
        self._ltp = QLabel("—")
        self._ltp.setStyleSheet("font-size: 22px; font-weight: bold;")
        self._change = QLabel("—")
        self._change_pct = QLabel("—")
        self._updated = QLabel("Last update: —")
        self._updated.setStyleSheet("color: gray; font-size: 11px;")
        self._status = QLabel("—")
        grid = QGridLayout(self)
        grid.addWidget(self._title, 0, 0, 1, 2)
        grid.addWidget(QLabel("LTP"), 1, 0)
        grid.addWidget(self._ltp, 1, 1)
        grid.addWidget(QLabel("Change"), 2, 0)
        grid.addWidget(self._change, 2, 1)
        grid.addWidget(QLabel("Change %"), 3, 0)
        grid.addWidget(self._change_pct, 3, 1)
        grid.addWidget(self._status, 4, 0, 1, 2)
        grid.addWidget(self._updated, 5, 0, 1, 2)

    def update_tick(self, payload: dict) -> None:
        """Update display from tick payload."""
        ltp = payload.get("ltp")
        change = payload.get("change")
        change_pct = payload.get("change_percent")
        timestamp = payload.get("timestamp")
        symbol = payload.get("symbol", "")
        self._ltp.setText(str(ltp) if ltp is not None else "—")
        self._change.setText(str(change) if change is not None else "—")
        self._change_pct.setText(
            f"{change_pct}%" if change_pct is not None else "—"
        )
        self._status.setText(f"{symbol} | Live")
        self._updated.setText(f"Last update: {self._format_ist_time(timestamp)}")

    @staticmethod
    def _format_ist_time(timestamp: str | None) -> str:
        return DateTimeHelper.format_ist(timestamp)

    def set_market_status(self, status: str) -> None:
        """Update market status label."""
        self._status.setText(status)

    def clear(self) -> None:
        """Reset widget."""
        self._ltp.setText("—")
        self._change.setText("—")
        self._change_pct.setText("—")
        self._updated.setText("Last update: —")
        self._status.setText("—")
