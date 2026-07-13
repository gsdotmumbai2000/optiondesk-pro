"""Market workspace ViewModel."""

from PySide6.QtCore import Property, Signal

from app.logging.logging_manager import get_logger
from app.market_data.diagnostics import log_tick_diagnostic
from app.ui.commands.ui_command import RelayCommand
from app.ui.viewmodels.base_viewmodel import BaseViewModel
from app.ui.viewmodels.context import ViewModelContext

logger = get_logger(__name__)

class MarketViewModel(BaseViewModel):
    """ViewModel for market workspace."""

    watchlist_changed = Signal(list)
    tick_updated = Signal(dict)
    market_status_changed = Signal(dict)

    def __init__(self, ctx: ViewModelContext, parent=None) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self._watchlist: list[str] = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]
        self._spot_symbol = "NIFTY"
        self._spot_price = "—"
        self._last_update = "—"
        self._market_status = "—"
        self._connection_status = "—"
        self.refresh_command = RelayCommand(self.refresh, parent=self)
        self._ctx.events.market_updated.connect(self._on_market_updated)
        self._ctx.events.tick_received.connect(self._on_tick)
        self._ctx.events.market_opened.connect(self._on_market_status)
        self._ctx.events.market_closed.connect(self._on_market_status)
        self._ctx.events.broker_connected.connect(lambda _: self._load_status())
        self._ctx.events.broker_disconnected.connect(lambda _: self._load_status())
        self._load_watchlist_only()

    @Property(list, notify=watchlist_changed)
    def watchlist(self) -> list[str]:
        return self._watchlist

    @Property(str, notify=tick_updated)
    def spot_price(self) -> str:
        return self._spot_price

    @Property(str, notify=tick_updated)
    def last_update(self) -> str:
        return self._last_update

    @Property(str, notify=market_status_changed)
    def market_status(self) -> str:
        return self._market_status

    @Property(str, notify=market_status_changed)
    def connection_status(self) -> str:
        return self._connection_status

    def refresh(self) -> None:
        self.busy = True

        def work():
            return self._ctx.provider.market.refresh_market(self._ctx.session_id)

        def done(result):
            self.busy = False
            self._load_status()
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

    def latest_tick_payload(self, symbol: str) -> dict:
        result = self._ctx.provider.market.latest_quote(
            self._ctx.session_id, symbol, "NSE"
        )
        return result.data if result and result.data else {}

    def _load_watchlist_only(self) -> None:
        """Load watchlist into memory without broker subscriptions."""
        result = self._ctx.provider.market.watchlist(
            self._ctx.session_id, tuple(self._watchlist)
        )
        self.watchlist_changed.emit(self._watchlist)
        if result:
            self.status_message = result.message
        self._load_status()

    def _load_status(self) -> None:
        result = self._ctx.provider.market.market_status(self._ctx.session_id)
        if not result or not result.data:
            return
        data = result.data
        self._market_status = str(data.get("status", "—"))
        self._connection_status = str(data.get("connection", "—"))
        self._last_update = str(data.get("last_tick", "—"))
        self.market_status_changed.emit(data)
        tick = self.latest_tick_payload(self._spot_symbol)
        if tick:
            self._apply_tick(tick)

    def _on_market_updated(self, payload: dict) -> None:
        self.status_message = "Market data updated"
        self._load_status()

    def _on_tick(self, payload: dict) -> None:
        tick = payload.get("tick", payload)
        log_tick_diagnostic(logger, "VIEWMODEL", "tick received", tick)
        if tick.get("symbol") == self._spot_symbol:
            self._apply_tick(tick)
        self.tick_updated.emit(tick)

    def _on_market_status(self, payload: dict) -> None:
        self._load_status()

    def _apply_tick(self, tick: dict) -> None:
        self._spot_price = str(tick.get("ltp", "—"))
        self._last_update = str(tick.get("timestamp", "—"))
        self.tick_updated.emit(tick)