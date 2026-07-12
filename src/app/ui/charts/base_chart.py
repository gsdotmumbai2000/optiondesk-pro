"""Chart framework placeholder."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.ui.models.ui_enums import ChartType


class ChartPlaceholder(QWidget):
    """Placeholder chart widget (no business calculations)."""

    def __init__(
        self,
        chart_type: ChartType,
        title: str = "",
        parent: QWidget | None = None,
    ) -> None:
        """Initialize chart placeholder."""
        super().__init__(parent)
        self._chart_type = chart_type
        self._title = title or chart_type.value.replace("_", " ").title()
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, _event) -> None:  # noqa: N802
        """Paint placeholder chart frame."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(8, 8, -8, -8)
        painter.setPen(QPen(QColor("#30363d"), 1, Qt.PenStyle.DashLine))
        painter.drawRect(rect)
        painter.setPen(QColor("#8b949e"))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self._title}\n[Chart Placeholder]")
