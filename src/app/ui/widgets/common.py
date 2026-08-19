"""Reusable UI widgets."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QLabel, QSplitter, QTableView, QVBoxLayout, QWidget


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


def style_splitter_handle(splitter: QSplitter) -> None:
    """Make a QSplitter's drag handle an actual visible line at rest, not
    just a few unstyled pixels you can only find by hunting with the mouse
    -- Qt's default Fusion handle has no idle-state color of its own, so
    it's easy to miss entirely on a table-heavy view. Colors are read from
    the splitter's own palette (Mid for idle, Highlight for hover) so this
    looks correct in light/dark/high-contrast alike, without hardcoding
    theme-specific hex values here."""
    palette = splitter.palette()
    idle = palette.color(QPalette.ColorRole.Mid).name()
    hover = palette.color(QPalette.ColorRole.Highlight).name()
    splitter.setHandleWidth(6)
    splitter.setStyleSheet(
        "QSplitter::handle { background-color: %s; }"
        "QSplitter::handle:hover { background-color: %s; }" % (idle, hover)
    )
