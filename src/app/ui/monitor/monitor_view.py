"""Position monitor view."""

from PySide6.QtWidgets import QVBoxLayout, QWidget

from app.ui.viewmodels.monitor_viewmodel import MonitorViewModel
from app.ui.widgets.common import DataTableWidget, SectionHeader


class MonitorView(QWidget):
    """Alerts, warnings, recommendations."""

    def __init__(self, viewmodel: MonitorViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = viewmodel
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Alerts"))
        self._alerts = DataTableWidget()
        layout.addWidget(self._alerts)
        layout.addWidget(SectionHeader("Warnings"))
        self._warnings = DataTableWidget()
        layout.addWidget(self._warnings)
        layout.addWidget(SectionHeader("Recommendations"))
        self._recs = DataTableWidget()
        layout.addWidget(self._recs)
        viewmodel.alerts_changed.connect(self._on_alerts)

    def _on_alerts(self, alerts: list) -> None:
        self._alerts.setToolTip(f"{len(alerts)} alerts")
