"""Trading workspace ViewModel."""

from PySide6.QtCore import Property, Signal

from app.application.models.enums import WorkspaceType
from app.ui.commands.ui_command import RelayCommand
from app.ui.viewmodels.base_viewmodel import BaseViewModel
from app.ui.viewmodels.context import ViewModelContext


class TradingViewModel(BaseViewModel):
    """ViewModel for trading workspace — Application Services only."""

    strategy_name_changed = Signal(str)
    summary_changed = Signal(str)

    def __init__(self, ctx: ViewModelContext, parent=None) -> None:
        """Initialize trading view model."""
        super().__init__(parent)
        self._ctx = ctx
        self._strategy_name = ""
        self._summary = "No strategy loaded"
        self.refresh_command = RelayCommand(self.refresh, parent=self)
        self.evaluate_command = RelayCommand(self.evaluate, parent=self)
        self.optimize_command = RelayCommand(self.optimize, parent=self)
        self.save_command = RelayCommand(self.save, parent=self)
        self.load_command = RelayCommand(self.load, parent=self)
        self.recommend_command = RelayCommand(self.generate_recommendation, parent=self)

    @Property(str, notify=strategy_name_changed)
    def strategy_name(self) -> str:
        return self._strategy_name

    @Property(str, notify=summary_changed)
    def summary(self) -> str:
        return self._summary

    def refresh(self) -> None:
        """Refresh trading workspace view."""
        view = self._ctx.provider.trading.view(self._ctx.session_id)
        self._summary = view.summary
        self.summary_changed.emit(self._summary)
        self.status_message = "Trading workspace refreshed"

    def evaluate(self) -> None:
        """Evaluate strategy (requires request from UI layer)."""
        self.status_message = "Evaluate: attach StrategyEvaluationRequest in view"

    def optimize(self) -> None:
        """Optimize strategy (requires request from UI layer)."""
        self.status_message = "Optimize: attach OptimizationRequest in view"

    def save(self) -> None:
        """Save current strategy placeholder."""
        self.status_message = "Save: provide strategy from builder"

    def load(self) -> None:
        """Navigate to strategy workspace."""
        self._ctx.provider.navigation.navigate(
            self._ctx.session_id,
            WorkspaceType.STRATEGY,
        )
        self.status_message = "Open strategy loader"

    def generate_recommendation(self) -> None:
        """Trigger AI recommendation flow."""
        self._ctx.provider.navigation.navigate(
            self._ctx.session_id,
            WorkspaceType.AI,
        )
        self.status_message = "Navigate to AI workspace"

    def on_strategy_updated(self, payload: dict) -> None:
        """Handle strategy update event."""
        name = payload.get("strategy_id", "")
        self._strategy_name = name
        self.strategy_name_changed.emit(name)
