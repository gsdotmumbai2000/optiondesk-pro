"""Broker connection indicator widget."""

from typing import TypeAlias

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget

from app.brokers.shared.enums import BrokerConnectionStatus

ConnectionStatusInput: TypeAlias = BrokerConnectionStatus | str


def normalize_connection_status(status: ConnectionStatusInput) -> BrokerConnectionStatus:
    """Coerce enum or string input to BrokerConnectionStatus."""
    if isinstance(status, BrokerConnectionStatus):
        return status
    if not isinstance(status, str):
        return BrokerConnectionStatus.DISCONNECTED
    for member in BrokerConnectionStatus:
        if member.value == status:
            return member
    key = status.upper().replace(" ", "_")
    if key in BrokerConnectionStatus.__members__:
        return BrokerConnectionStatus[key]
    return BrokerConnectionStatus.DISCONNECTED


def connection_status_label(status: ConnectionStatusInput) -> str:
    """Return user-facing status label without assuming enum input."""
    if isinstance(status, BrokerConnectionStatus):
        return status.value
    if isinstance(status, str) and status:
        return status
    return BrokerConnectionStatus.DISCONNECTED.value


class ConnectionIndicator(QWidget):
    """Status bar connection indicator with color coding."""

    _COLORS: dict[BrokerConnectionStatus, str] = {
        BrokerConnectionStatus.CONNECTED: "#2ecc71",
        BrokerConnectionStatus.CONNECTING: "#f39c12",
        BrokerConnectionStatus.DISCONNECTED: "#95a5a6",
        BrokerConnectionStatus.AUTHENTICATION_FAILED: "#e74c3c",
        BrokerConnectionStatus.EXPIRED: "#e67e22",
        BrokerConnectionStatus.RECONNECT_REQUIRED: "#e67e22",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize indicator."""
        super().__init__(parent)
        self._dot = QLabel("●")
        self._label = QLabel("Broker: Disconnected")
        self._dot.setFixedWidth(16)
        layout = self.layout() if self.layout() else None
        if layout is None:
            from PySide6.QtWidgets import QHBoxLayout

            box = QHBoxLayout(self)
            box.setContentsMargins(0, 0, 8, 0)
            box.addWidget(self._dot)
            box.addWidget(self._label)
        self.set_color(BrokerConnectionStatus.DISCONNECTED)

    def update_status(
        self,
        broker_name: str,
        status: ConnectionStatusInput,
        user_id: str,
        environment: str,
    ) -> None:
        """Update indicator text and color."""
        user = user_id or "—"
        env = environment.title() if environment else "—"
        label = connection_status_label(status)
        self._label.setText(f"{broker_name} | {label} | {user} | {env}")
        self.set_color(status)

    def set_color(self, status: ConnectionStatusInput) -> None:
        """Set indicator dot color."""
        normalized = normalize_connection_status(status)
        color = self._COLORS.get(normalized, "#95a5a6")
        self._dot.setStyleSheet(f"color: {color}; font-size: 14px;")
        self._dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
