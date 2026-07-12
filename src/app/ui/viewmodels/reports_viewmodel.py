"""Reports workspace ViewModel."""

from PySide6.QtCore import Property, Signal

from app.ui.commands.ui_command import RelayCommand
from app.ui.viewmodels.base_viewmodel import BaseViewModel
from app.ui.viewmodels.context import ViewModelContext


class ReportsViewModel(BaseViewModel):
    """ViewModel for reports workspace."""

    reports_changed = Signal(list)

    def __init__(self, ctx: ViewModelContext, parent=None) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self._reports: list[str] = []
        self.refresh_command = RelayCommand(self.refresh, parent=self)
        self.export_command = RelayCommand(self.export, parent=self)

    @Property(list, notify=reports_changed)
    def reports(self) -> list[str]:
        return self._reports

    def refresh(self) -> None:
        keys = [
            f"{self._ctx.session_id}:portfolio-report",
            f"{self._ctx.session_id}:backtest-report",
        ]
        self._reports = [k for k in keys if self._ctx.provider.cache.get_report(k)]
        self.reports_changed.emit(self._reports)
        self.status_message = f"{len(self._reports)} reports available"

    def export(self) -> None:
        self.status_message = "Export report via portfolio or backtest workspace"
