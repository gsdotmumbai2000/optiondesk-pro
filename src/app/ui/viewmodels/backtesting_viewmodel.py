"""Backtesting workspace ViewModel."""

from PySide6.QtCore import Property, Signal

from app.ui.commands.ui_command import RelayCommand
from app.ui.viewmodels.base_viewmodel import BaseViewModel
from app.ui.viewmodels.context import ViewModelContext


class BacktestingViewModel(BaseViewModel):
    """ViewModel for backtesting workspace."""

    run_state_changed = Signal(str)

    def __init__(self, ctx: ViewModelContext, parent=None) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self._run_state = "IDLE"
        self.run_command = RelayCommand(self.run_backtest, parent=self)
        self.pause_command = RelayCommand(self.pause, parent=self)
        self.resume_command = RelayCommand(self.resume, parent=self)
        self.stop_command = RelayCommand(self.stop, parent=self)
        self.export_command = RelayCommand(self.export, parent=self)

    @Property(str, notify=run_state_changed)
    def run_state(self) -> str:
        return self._run_state

    def run_backtest(self) -> None:
        self._ctx.provider.coordinator.notify_backtest_started(self._ctx.session_id)
        self.status_message = "Run backtest: attach BacktestRequest in view"

    def pause(self) -> None:
        view = self._ctx.provider.backtesting.pause(self._ctx.session_id)
        self._run_state = view.state
        self.run_state_changed.emit(self._run_state)

    def resume(self) -> None:
        view = self._ctx.provider.backtesting.resume(self._ctx.session_id)
        self._run_state = view.state
        self.run_state_changed.emit(self._run_state)

    def stop(self) -> None:
        view = self._ctx.provider.backtesting.stop(self._ctx.session_id)
        self._run_state = view.state
        self.run_state_changed.emit(self._run_state)

    def export(self) -> None:
        result = self._ctx.provider.backtesting.export_results(self._ctx.session_id)
        self.status_message = result.message
