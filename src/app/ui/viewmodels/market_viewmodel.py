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
    option_chain_changed = Signal(list)

    def __init__(self, ctx: ViewModelContext, parent=None) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self._watchlist: list[str] = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]
        self._spot_symbol = "NIFTY"
        self._spot_price = "—"
        self._last_update = "—"
        self._market_status = "—"
        self._connection_status = "—"
        self._option_chain_underlying = ""
        self._option_chain_exchange = ""
        self._option_chain_expiry = ""
        self._broker_ready = False
        self._option_chain_auto_requested = False
        self.refresh_command = RelayCommand(self.refresh, parent=self)
        self._ctx.events.market_updated.connect(self._on_market_updated)
        self._ctx.events.tick_received.connect(self._on_tick)
        self._ctx.events.market_opened.connect(self._on_market_status)
        self._ctx.events.market_closed.connect(self._on_market_status)
        self._ctx.events.broker_connected.connect(self._on_broker_ready)
        self._ctx.events.authentication_succeeded.connect(self._on_broker_ready)
        self._ctx.events.broker_disconnected.connect(self._on_broker_disconnected)
        self._ctx.events.option_chain_updated.connect(self._on_option_chain_event)
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

    def load_option_chain(self, underlying: str = "NIFTY", *, exchange: str = "NFO") -> None:
        """Load the initial ATM-centered option chain snapshot asynchronously.

        Performs a broker REST call and subscribes the live strike window,
        so it always runs on the BackgroundWorker thread pool rather than
        blocking the Qt UI thread. Requires an already-connected broker
        session; call after broker_connected/authentication_succeeded.
        """
        logger.info("Option chain load requested")
        if not self._broker_ready:
            logger.info("Option chain load skipped: broker not connected")
            return
        self.busy = True

        def work():
            logger.info("Option chain load started")
            return self._ctx.provider.market.initial_option_chain(
                self._ctx.session_id, underlying, exchange=exchange
            )

        def done(result):
            self.busy = False
            if not result or not result.success:
                message = result.message if result else "Option chain unavailable"
                logger.warning("Option chain load failed: {error}", error=message)
                self.status_message = message
                return
            data = result.data or {}
            self._option_chain_underlying = str(data.get("underlying", underlying))
            self._option_chain_exchange = str(data.get("exchange", exchange))
            self._option_chain_expiry = str(data.get("expiry_date", ""))
            self.option_chain_changed.emit(self._rows_from_rest_strikes(data.get("strikes", [])))
            logger.debug("UI result emitted: option_chain_changed")
            self.status_message = result.message
            logger.info(
                "Option chain load completed: strikes={count}",
                count=len(data.get("strikes", [])),
            )

        def err(msg: str):
            self.busy = False
            logger.warning("Option chain load failed: {error}", error=msg)
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

    def _on_broker_ready(self, payload: dict) -> None:
        """Handle broker_connected/authentication_succeeded: enable and trigger load once."""
        self._broker_ready = True
        self._load_status()
        if self._option_chain_auto_requested:
            return
        self._option_chain_auto_requested = True
        self.load_option_chain()

    def _on_broker_disconnected(self, payload: dict) -> None:
        self._broker_ready = False
        self._option_chain_auto_requested = False
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

    def _on_option_chain_event(self, payload: dict) -> None:
        chain = payload.get("chain")
        if not isinstance(chain, dict):
            return
        if (
            chain.get("underlying") != self._option_chain_underlying
            or chain.get("exchange") != self._option_chain_exchange
            or chain.get("expiry_date") != self._option_chain_expiry
        ):
            return
        self.option_chain_changed.emit(self._rows_from_live_chain(chain))

    @staticmethod
    def _rows_from_rest_strikes(strikes: list) -> list[tuple]:
        """Build (Type, Strike, OI, Volume, IV, Delta, Gamma, Theta, Vega) rows."""
        rows: list[tuple] = []
        for strike in strikes:
            if not isinstance(strike, dict):
                continue
            price = strike.get("strike_price", "—")
            rows.append(_option_row("CE", price, strike, "call"))
            rows.append(_option_row("PE", price, strike, "put"))
        return rows

    @staticmethod
    def _rows_from_live_chain(chain: dict) -> list[tuple]:
        """Build display rows from a LiveOptionChain event payload."""
        strikes = chain.get("strikes", {})
        rows: list[tuple] = []
        for row in strikes.values() if isinstance(strikes, dict) else []:
            if not isinstance(row, dict):
                continue
            price = row.get("strike_price", "—")
            call = row.get("call") or {}
            put = row.get("put") or {}
            rows.append(_live_option_row("CE", price, call))
            rows.append(_live_option_row("PE", price, put))
        return rows


def _option_row(side: str, strike_price, strike: dict, prefix: str) -> tuple:
    def field(name: str):
        value = strike.get(f"{prefix}_{name}")
        return str(value) if value is not None else "—"

    return (
        side,
        str(strike_price),
        field("oi"),
        field("volume"),
        field("iv"),
        "—",
        "—",
        "—",
        "—",
    )


def _live_option_row(side: str, strike_price, leg: dict) -> tuple:
    def field(name: str):
        value = leg.get(name)
        return str(value) if value is not None else "—"

    return (
        side,
        str(strike_price),
        field("open_interest"),
        field("volume"),
        field("implied_volatility"),
        "—",
        "—",
        "—",
        "—",
    )