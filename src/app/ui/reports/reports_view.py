"""Reports view."""

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from app.ui.viewmodels.reports_viewmodel import ReportsViewModel
from app.ui.widgets.common import DataTableWidget, SectionHeader


class ReportsView(QWidget):
    """Reports list, export, history."""

    def __init__(self, viewmodel: ReportsViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = viewmodel
        layout = QVBoxLayout(self)
        btns = QHBoxLayout()
        ref = QPushButton("Refresh")
        ref.clicked.connect(viewmodel.refresh_command.execute)
        exp = QPushButton("Export")
        exp.clicked.connect(viewmodel.export_command.execute)
        btns.addWidget(ref)
        btns.addWidget(exp)
        layout.addLayout(btns)
        layout.addWidget(SectionHeader("Reports"))
        self._table = DataTableWidget()
        layout.addWidget(self._table)
        layout.addWidget(SectionHeader("History"))
