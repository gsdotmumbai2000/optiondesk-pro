"""Tests for MarketView tick routing between the Spot widget and Watchlist."""

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from app.ui.market.market_view import MarketView


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Provide a Qt application instance for widget tests."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class _FakeMarketViewModel(QObject):
    """Minimal MarketViewModel double exposing only the signals MarketView needs."""

    watchlist_changed = Signal(list)
    tick_updated = Signal(dict)
    market_status_changed = Signal(dict)
    option_chain_changed = Signal(list)
    option_chain_snapshot_changed = Signal(object)
    expiries_changed = Signal(list)
    expiry_selected = Signal(str)

    def __init__(self, watchlist: list[str]) -> None:
        super().__init__()
        self.watchlist = watchlist
        self.available_expiries: list[tuple[str, str]] = []
        self.load_option_chain_calls: list[tuple] = []
        self.set_chain_width_calls: list[int] = []
        self.set_expiry_calls: list[str] = []

    def load_option_chain(self, underlying: str = "NIFTY", *, exchange: str = "NFO") -> None:
        """No-op: MarketView must call this without blocking construction."""
        self.load_option_chain_calls.append((underlying, exchange))

    def set_chain_width(self, radius: int) -> None:
        self.set_chain_width_calls.append(radius)

    def set_expiry(self, expiry_date: str) -> None:
        self.set_expiry_calls.append(expiry_date)


def _make_view(qapp: QApplication) -> MarketView:
    viewmodel = _FakeMarketViewModel(["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"])
    return MarketView(viewmodel)


class TestMarketViewDoesNotEagerlyLoadOptionChain:
    """MarketView must not call load_option_chain() from its constructor.

    The broker session may not be connected yet at construction time
    (MainWindow builds ViewModels/workspaces before broker session restore
    runs), so eagerly calling load_option_chain() here would always fail.
    MarketViewModel now triggers the load itself once the broker session is
    actually connected/authenticated.
    """

    def test_construction_does_not_call_load_option_chain(self, qapp: QApplication) -> None:
        viewmodel = _FakeMarketViewModel(["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"])

        MarketView(viewmodel)

        assert viewmodel.load_option_chain_calls == []


def _watchlist_ltp(view: MarketView, symbol: str) -> str:
    row = view._symbol_rows[symbol]
    return view._watchlist_model.item(row, 1).text()


class TestMarketViewSpotFiltering:
    """NIFTY Spot widget only reflects NIFTY cash-index ticks."""

    def test_nifty_tick_updates_spot_widget(self, qapp: QApplication) -> None:
        view = _make_view(qapp)

        view._on_tick({"tick": {"symbol": "NIFTY", "exchange": "NSE", "ltp": "24502.1"}})

        assert view._spot._ltp.text() == "24502.1"

    def test_banknifty_tick_does_not_update_spot_widget(self, qapp: QApplication) -> None:
        view = _make_view(qapp)

        view._on_tick({"tick": {"symbol": "BANKNIFTY", "exchange": "NSE", "ltp": "51000"}})

        assert view._spot._ltp.text() == "—"

    def test_finnifty_tick_does_not_update_spot_widget(self, qapp: QApplication) -> None:
        view = _make_view(qapp)

        view._on_tick({"tick": {"symbol": "FINNIFTY", "exchange": "NSE", "ltp": "23000"}})

        assert view._spot._ltp.text() == "—"

    def test_midcpnifty_tick_does_not_update_spot_widget(self, qapp: QApplication) -> None:
        view = _make_view(qapp)

        view._on_tick({"tick": {"symbol": "MIDCPNIFTY", "exchange": "NSE", "ltp": "14937.5"}})

        assert view._spot._ltp.text() == "—"

    def test_non_nifty_tick_does_not_overwrite_prior_nifty_spot_value(
        self, qapp: QApplication
    ) -> None:
        view = _make_view(qapp)

        view._on_tick({"tick": {"symbol": "NIFTY", "exchange": "NSE", "ltp": "24502.1"}})
        view._on_tick({"tick": {"symbol": "MIDCPNIFTY", "exchange": "NSE", "ltp": "14937.5"}})

        assert view._spot._ltp.text() == "24502.1"

    def test_nifty_futures_tick_does_not_update_spot_widget(self, qapp: QApplication) -> None:
        """Regression test: NIFTY futures ticks are canonicalized to the same
        bare "NIFTY" symbol as the spot tick (see
        websocket_service._canonicalize_future_tick), but carry exchange
        "NFO" instead of "NSE". Without the exchange check, a futures LTP
        would flow into the spot widget, making the displayed NIFTY spot
        price flicker/spike against the futures premium/discount."""
        view = _make_view(qapp)

        view._on_tick({"tick": {"symbol": "NIFTY", "exchange": "NSE", "ltp": "24502.1"}})
        view._on_tick({"tick": {"symbol": "NIFTY", "exchange": "NFO", "ltp": "24610.0"}})

        assert view._spot._ltp.text() == "24502.1"


class TestMarketViewWatchlistUnaffected:
    """Watchlist row updates continue to work regardless of the Spot filter."""

    def test_watchlist_row_updates_for_each_symbol(self, qapp: QApplication) -> None:
        view = _make_view(qapp)

        view._on_tick({"tick": {"symbol": "NIFTY", "exchange": "NSE", "ltp": "24502.1"}})
        view._on_tick({"tick": {"symbol": "BANKNIFTY", "exchange": "NSE", "ltp": "51000"}})
        view._on_tick({"tick": {"symbol": "FINNIFTY", "exchange": "NSE", "ltp": "23000"}})
        view._on_tick({"tick": {"symbol": "MIDCPNIFTY", "exchange": "NSE", "ltp": "14937.5"}})

        assert _watchlist_ltp(view, "NIFTY") == "24502.1"
        assert _watchlist_ltp(view, "BANKNIFTY") == "51000"
        assert _watchlist_ltp(view, "FINNIFTY") == "23000"
        assert _watchlist_ltp(view, "MIDCPNIFTY") == "14937.5"

    def test_unknown_symbol_tick_does_not_raise(self, qapp: QApplication) -> None:
        view = _make_view(qapp)

        view._on_tick({"tick": {"symbol": "RELIANCE", "exchange": "NSE", "ltp": "2900"}})

    def test_banknifty_futures_tick_does_not_overwrite_watchlist_row(
        self, qapp: QApplication
    ) -> None:
        """Same collision as the spot widget, but for a non-NIFTY watchlist
        row: BANKNIFTY futures ticks are also canonicalized to the bare
        "BANKNIFTY" symbol (exchange "NFO"), so the exchange check must
        guard the watchlist row lookup too."""
        view = _make_view(qapp)

        view._on_tick({"tick": {"symbol": "BANKNIFTY", "exchange": "NSE", "ltp": "51000"}})
        view._on_tick({"tick": {"symbol": "BANKNIFTY", "exchange": "NFO", "ltp": "51250"}})

        assert _watchlist_ltp(view, "BANKNIFTY") == "51000"
