"""Monitor view ViewModel."""

from PySide6.QtCore import Property, Signal

from app.ui.viewmodels.base_viewmodel import BaseViewModel
from app.ui.viewmodels.context import ViewModelContext


class MonitorViewModel(BaseViewModel):
    """ViewModel for position monitor panel."""

    alerts_changed = Signal(list)
    warnings_changed = Signal(list)
    recommendations_changed = Signal(list)

    def __init__(self, ctx: ViewModelContext, parent=None) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self._alerts: list = []
        self._warnings: list = []
        self._recommendations: list = []
        self._ctx.events.alert_raised.connect(self._on_alert)

    @Property(list, notify=alerts_changed)
    def alerts(self) -> list:
        return self._alerts

    @Property(list, notify=warnings_changed)
    def warnings(self) -> list:
        return self._warnings

    @Property(list, notify=recommendations_changed)
    def recommendations(self) -> list:
        return self._recommendations

    def refresh_from_monitor_result(self, monitor_result) -> None:
        """Update from MonitorResult (no calculations)."""
        if monitor_result is None:
            return
        self._alerts = list(monitor_result.open_alerts)
        self.alerts_changed.emit(self._alerts)
        self._warnings = list(monitor_result.warning_alerts)
        self.warnings_changed.emit(self._warnings)
        self._recommendations = list(monitor_result.recommendation_list)
        self.recommendations_changed.emit(self._recommendations)
        self.status_message = f"{len(self._alerts)} open alerts"

    def _on_alert(self, payload: dict) -> None:
        self.status_message = f"Alert: {payload.get('alert_id', '')}"
