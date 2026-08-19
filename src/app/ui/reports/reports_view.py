"""Reports view."""

from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from app.ui.viewmodels.reports_viewmodel import ReportsViewModel
from app.ui.widgets.common import DataTableWidget, SectionHeader

_HEADERS = ("Report",)


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
        self._table_model = QStandardItemModel(0, len(_HEADERS), self)
        self._table_model.setHorizontalHeaderLabels(list(_HEADERS))
        self._table.setModel(self._table_model)
        layout.addWidget(self._table)
        viewmodel.reports_changed.connect(self._on_reports)
        layout.addWidget(SectionHeader("History"))

    def _on_reports(self, reports: list) -> None:
        self._table_model.setRowCount(0)
        for report_key in reports:
            self._table_model.appendRow([QStandardItem(str(report_key))])
