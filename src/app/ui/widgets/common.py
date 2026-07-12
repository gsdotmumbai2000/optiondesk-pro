"""Reusable UI widgets."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QTableView, QVBoxLayout, QWidget


class SectionHeader(QWidget):
    """Section header label."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        """Initialize header."""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold; font-size: 13px; color: #8b949e;")
        layout.addWidget(label)


class DataTableWidget(QTableView):
    """Styled table for model/view data."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize table."""
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSortingEnabled(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
