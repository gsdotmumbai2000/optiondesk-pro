"""Market workspace ViewModel."""

from PySide6.QtCore import Property, Signal

from app.ui.commands.ui_command import RelayCommand
from app.ui.viewmodels.base_viewmodel import BaseViewModel
from app.ui.viewmodels.context import ViewModelContext


class MarketViewModel(BaseViewModel):
    """ViewModel for market workspace."""

    watchlist_changed = Signal(list)

    def __init__(self, ctx: ViewModelContext, parent=None) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self._watchlist: list[str] = []
        self.refresh_command = RelayCommand(self.refresh, parent=self)
        self._ctx.events.market_updated.connect(self._on_market_updated)

    @Property(list, notify=watchlist_changed)
    def watchlist(self) -> list[str]:
        return self._watchlist

    def refresh(self) -> None:
        self.busy = True

        def work():
            return self._ctx.provider.market.refresh_market(self._ctx.session_id)

        def done(result):
            self.busy = False
            self.status_message = result.message if result else "Market refreshed"

        def err(msg: str):
            self.busy = False
            self.set_error(msg)

        self._ctx.worker.run(work, done, err)

    def set_watchlist(self, symbols: list[str]) -> None:
        result = self._ctx.provider.market.watchlist(self._ctx.session_id, tuple(symbols))
        self._watchlist = list(symbols)
        self.watchlist_changed.emit(self._watchlist)
        self.status_message = result.message

    def load_overview(self):
        return self._ctx.provider.market.market_overview(self._ctx.session_id)

    def _on_market_updated(self, payload: dict) -> None:
        self.status_message = "Market data updated"
        self.refresh()
