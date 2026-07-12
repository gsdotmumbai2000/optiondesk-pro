"""Portfolio workspace ViewModel."""

from PySide6.QtCore import Property, Signal

from app.ui.commands.ui_command import RelayCommand
from app.ui.viewmodels.base_viewmodel import BaseViewModel
from app.ui.viewmodels.context import ViewModelContext


class PortfolioViewModel(BaseViewModel):
    """ViewModel for portfolio workspace."""

    summary_changed = Signal(str)

    def __init__(self, ctx: ViewModelContext, parent=None) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self._summary = ""
        self.refresh_command = RelayCommand(self.refresh, parent=self)
        self.export_command = RelayCommand(self.export_report, parent=self)
        self._ctx.events.portfolio_updated.connect(self._on_portfolio_updated)

    @Property(str, notify=summary_changed)
    def summary(self) -> str:
        return self._summary

    def load_portfolio(self, portfolio_id: str) -> None:
        result = self._ctx.provider.portfolio.load_portfolio(
            self._ctx.session_id,
            portfolio_id,
        )
        if result.success:
            self._ctx.provider.coordinator.notify_portfolio_loaded(portfolio_id)
        self.status_message = result.message

    def refresh(self) -> None:
        view = self._ctx.provider.portfolio.view(self._ctx.session_id)
        self._summary = view.summary
        self.summary_changed.emit(self._summary)
        self.status_message = "Portfolio view refreshed"

    def export_report(self) -> None:
        result = self._ctx.provider.portfolio.export_report(
            self._ctx.session_id,
            f"{self._ctx.session_id}:portfolio-report",
        )
        self.status_message = result.message

    def _on_portfolio_updated(self, _payload: dict) -> None:
        self.refresh()
