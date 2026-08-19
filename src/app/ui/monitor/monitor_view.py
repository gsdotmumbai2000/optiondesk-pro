"""Position monitor view."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from app.ui.viewmodels.monitor_viewmodel import MonitorViewModel
from app.ui.widgets.common import DataTableWidget, SectionHeader, style_splitter_handle

_ALERT_HEADERS = ("Priority", "Title", "Symbol", "Message", "Raised At")
_RECOMMENDATION_HEADERS = ("Type", "Symbol", "Title", "Suggested Action", "Confidence")


class MonitorView(QWidget):
    """Alerts, warnings, recommendations -- each in its own vertically
    resizable pane (drag the handle between any two to reallocate space),
    rather than three tables fixed to whatever share a plain stacked
    layout happens to give them."""

    def __init__(self, viewmodel: MonitorViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = viewmodel
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Vertical)
        outer.addWidget(splitter)

        self._alerts = DataTableWidget()
        self._alerts_model = self._new_alert_model()
        self._alerts.setModel(self._alerts_model)
        splitter.addWidget(self._pane("Alerts", self._alerts))

        self._warnings = DataTableWidget()
        self._warnings_model = self._new_alert_model()
        self._warnings.setModel(self._warnings_model)
        splitter.addWidget(self._pane("Warnings", self._warnings))

        self._recs = DataTableWidget()
        self._recs_model = QStandardItemModel(0, len(_RECOMMENDATION_HEADERS), self)
        self._recs_model.setHorizontalHeaderLabels(list(_RECOMMENDATION_HEADERS))
        self._recs.setModel(self._recs_model)
        splitter.addWidget(self._pane("Recommendations", self._recs))

        for index in range(splitter.count()):
            splitter.setStretchFactor(index, 1)
        style_splitter_handle(splitter)

        viewmodel.alerts_changed.connect(lambda alerts: self._on_alerts(self._alerts_model, alerts))
        viewmodel.warnings_changed.connect(lambda alerts: self._on_alerts(self._warnings_model, alerts))
        viewmodel.recommendations_changed.connect(self._on_recommendations)

    def _pane(self, title: str, table: DataTableWidget) -> QWidget:
        """One splitter pane: a section header stacked over its table."""
        pane = QWidget()
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(SectionHeader(title))
        layout.addWidget(table)
        return pane

    def _new_alert_model(self) -> QStandardItemModel:
        model = QStandardItemModel(0, len(_ALERT_HEADERS), self)
        model.setHorizontalHeaderLabels(list(_ALERT_HEADERS))
        return model

    def _on_alerts(self, model: QStandardItemModel, alerts: list) -> None:
        model.setRowCount(0)
        for alert in alerts:
            model.appendRow([
                QStandardItem(alert.priority.value),
                QStandardItem(alert.title),
                QStandardItem(alert.symbol),
                QStandardItem(alert.message),
                QStandardItem(str(alert.raised_at)),
            ])

    def _on_recommendations(self, recommendations: list) -> None:
        self._recs_model.setRowCount(0)
        for rec in recommendations:
            self._recs_model.appendRow([
                QStandardItem(rec.recommendation_type.value),
                QStandardItem(rec.symbol),
                QStandardItem(rec.title),
                QStandardItem(rec.suggested_action),
                QStandardItem(str(rec.confidence)),
            ])
