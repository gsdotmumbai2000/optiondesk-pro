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

    def __init__(self, watchlist: list[str]) -> None:
        super().__init__()
        self.watchlist = watchlist
        self.load_option_chain_calls: list[tuple] = []

    def load_option_chain(self, underlying: str = "NIFTY", *, exchange: str = "NFO") -> None:
        """No-op: MarketView must call this without blocking construction."""
        self.load_option_chain_calls.append((underlying, exchange))


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
    """NIFTY Spot widget only reflects NIFTY ticks."""

    def test_nifty_tick_updates_spot_widget(self, qapp: QApplication) -> None:
        view = _make_view(qapp)

        view._on_tick({"tick": {"symbol": "NIFTY", "ltp": "24502.1"}})

        assert view._spot._ltp.text() == "24502.1"

    def test_banknifty_tick_does_not_update_spot_widget(self, qapp: QApplication) -> None:
        view = _make_view(qapp)

        view._on_tick({"tick": {"symbol": "BANKNIFTY", "ltp": "51000"}})

        assert view._spot._ltp.text() == "—"

    def test_finnifty_tick_does_not_update_spot_widget(self, qapp: QApplication) -> None:
        view = _make_view(qapp)

        view._on_tick({"tick": {"symbol": "FINNIFTY", "ltp": "23000"}})

        assert view._spot._ltp.text() == "—"

    def test_midcpnifty_tick_does_not_update_spot_widget(self, qapp: QApplication) -> None:
        view = _make_view(qapp)

        view._on_tick({"tick": {"symbol": "MIDCPNIFTY", "ltp": "14937.5"}})

        assert view._spot._ltp.text() == "—"

    def test_non_nifty_tick_does_not_overwrite_prior_nifty_spot_value(
        self, qapp: QApplication
    ) -> None:
        view = _make_view(qapp)

        view._on_tick({"tick": {"symbol": "NIFTY", "ltp": "24502.1"}})
        view._on_tick({"tick": {"symbol": "MIDCPNIFTY", "ltp": "14937.5"}})

        assert view._spot._ltp.text() == "24502.1"


class TestMarketViewWatchlistUnaffected:
    """Watchlist row updates continue to work regardless of the Spot filter."""

    def test_watchlist_row_updates_for_each_symbol(self, qapp: QApplication) -> None:
        view = _make_view(qapp)

        view._on_tick({"tick": {"symbol": "NIFTY", "ltp": "24502.1"}})
        view._on_tick({"tick": {"symbol": "BANKNIFTY", "ltp": "51000"}})
        view._on_tick({"tick": {"symbol": "FINNIFTY", "ltp": "23000"}})
        view._on_tick({"tick": {"symbol": "MIDCPNIFTY", "ltp": "14937.5"}})

        assert _watchlist_ltp(view, "NIFTY") == "24502.1"
        assert _watchlist_ltp(view, "BANKNIFTY") == "51000"
        assert _watchlist_ltp(view, "FINNIFTY") == "23000"
        assert _watchlist_ltp(view, "MIDCPNIFTY") == "14937.5"

    def test_unknown_symbol_tick_does_not_raise(self, qapp: QApplication) -> None:
        view = _make_view(qapp)

        view._on_tick({"tick": {"symbol": "RELIANCE", "ltp": "2900"}})
