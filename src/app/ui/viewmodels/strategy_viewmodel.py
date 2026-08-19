"""Strategy workspace ViewModel."""

from PySide6.QtCore import Property, Signal

from app.logging.logging_manager import get_logger
from app.ui.commands.ui_command import RelayCommand
from app.ui.models.ui_enums import UIWorkspaceId
from app.ui.viewmodels.base_viewmodel import BaseViewModel
from app.ui.viewmodels.context import ViewModelContext

logger = get_logger(__name__)


class StrategyViewModel(BaseViewModel):
    """ViewModel for strategy workspace."""

    strategies_changed = Signal(list)
    workspace_switch_requested = Signal(str)

    def __init__(self, ctx: ViewModelContext, parent=None) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self._strategies: list = []
        self.open_command = RelayCommand(self.open_selected, parent=self)
        self.save_command = RelayCommand(self.save, parent=self)
        self.refresh_command = RelayCommand(self.refresh, parent=self)
        self._ctx.events.strategy_updated.connect(self._on_strategy_updated)

    @Property(list, notify=strategies_changed)
    def strategies(self) -> list:
        return self._strategies

    def refresh(self) -> None:
        result = self._ctx.provider.strategy.list_strategies(self._ctx.session_id)
        self._strategies = list(result.data or [])
        self.strategies_changed.emit(self._strategies)
        self.status_message = result.message

    def open_selected(self) -> None:
        self.status_message = "Select strategy to open"

    def open_strategy(self, strategy_id: str) -> None:
        """Open a saved strategy: mark it active in both the Strategy and
        Trading workspaces (Trading's evaluate/optimize/paper-trade/margin
        actions only ever look at the Trading workspace's active entity_id,
        so it must be set here for those to find anything), then switch the
        UI to the Trading tab where it's actually usable."""
        logger.debug("open_strategy: entering strategy_id={strategy_id}", strategy_id=strategy_id)
        result = self._ctx.provider.strategy.load_strategy(
            self._ctx.session_id,
            strategy_id,
        )
        logger.debug(
            "open_strategy: strategy.load_strategy returned success={success} message={message}",
            success=result.success,
            message=result.message,
        )
        if not result.success:
            self.status_message = result.message
            return
        trading_result = self._ctx.provider.trading.load_strategy(
            self._ctx.session_id,
            strategy_id,
        )
        logger.debug(
            "open_strategy: trading.load_strategy returned success={success} message={message}",
            success=trading_result.success,
            message=trading_result.message,
        )
        self._ctx.provider.coordinator.notify_strategy_loaded(strategy_id)
        logger.debug("open_strategy: coordinator notified")
        self.status_message = trading_result.message
        if trading_result.success:
            logger.debug("open_strategy: emitting workspace_switch_requested TRADING")
            self.workspace_switch_requested.emit(UIWorkspaceId.TRADING.value)

    def save(self) -> None:
        self.status_message = "Save strategy from builder"

    def _on_strategy_updated(self, _payload: dict) -> None:
        self.refresh()
