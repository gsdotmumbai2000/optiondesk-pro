"""Tests for MarketViewModel option-chain load gating on broker readiness.

Covers the startup-order fix: MarketView no longer calls load_option_chain()
from its constructor, and MarketViewModel instead loads the option chain
only after the broker session is actually connected/authenticated, exactly
once per connection.
"""

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult
from app.ui.viewmodels.context import ViewModelContext
from app.ui.viewmodels.market_viewmodel import MarketViewModel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Provide a Qt application instance for ViewModel signal tests."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class _FakeEventBridge(QObject):
    """Minimal UIEventBridge double exposing only the signals MarketViewModel needs."""

    market_updated = Signal(dict)
    tick_received = Signal(dict)
    market_opened = Signal(dict)
    market_closed = Signal(dict)
    broker_connected = Signal(dict)
    authentication_succeeded = Signal(dict)
    broker_disconnected = Signal(dict)
    option_chain_updated = Signal(dict)


class _FakeMarketService:
    """Minimal MarketWorkspaceService double."""

    def __init__(self) -> None:
        self.initial_option_chain_calls: list[tuple] = []

    def watchlist(self, session_id: str, symbols: tuple) -> WorkspaceOperationResult:
        return WorkspaceOperationResult(True, WorkspaceType.MARKET, "Watchlist loaded", symbols)

    def market_status(self, session_id: str) -> WorkspaceOperationResult:
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            "status",
            {"status": "OPEN", "connection": "Connected", "last_tick": ""},
        )

    def latest_quote(self, session_id: str, symbol: str, exchange: str) -> WorkspaceOperationResult:
        return WorkspaceOperationResult(False, WorkspaceType.MARKET, "no tick", {})

    def list_expiries(
        self, session_id: str, underlying: str = "NIFTY", *, exchange: str = "NFO"
    ) -> WorkspaceOperationResult:
        return WorkspaceOperationResult(
            True, WorkspaceType.MARKET, "1 expiry",
            [{"label": "28-Aug-2026 (Weekly)", "expiry_date": "28-Aug-2026"}],
        )

    def initial_option_chain(
        self,
        session_id: str,
        underlying: str = "NIFTY",
        *,
        exchange: str = "NFO",
        window_radius: int = 10,
        expiry_date: str = "",
    ) -> WorkspaceOperationResult:
        self.initial_option_chain_calls.append((session_id, underlying, exchange, window_radius))
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            f"Option chain for {underlying}",
            {"underlying": underlying, "exchange": exchange, "expiry_date": "", "strikes": []},
        )


class _FakeProvider:
    """Minimal ApplicationProvider double exposing only `.market`."""

    def __init__(self, market: _FakeMarketService) -> None:
        self.market = market


class _FakeWorker:
    """BackgroundWorker double that records dispatches instead of running threads."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def run(self, fn, on_finished, on_error) -> None:
        self.calls.append((fn, on_finished, on_error))

    def execute(self, index: int = -1) -> None:
        """Synchronously run a previously queued call, as the thread pool would."""
        fn, done, err = self.calls[index]
        try:
            result = fn()
        except Exception as exc:  # noqa: BLE001
            err(str(exc))
            return
        done(result)


def _make_viewmodel(
    qapp: QApplication,
) -> tuple[MarketViewModel, _FakeWorker, _FakeMarketService, _FakeEventBridge]:
    market = _FakeMarketService()
    provider = _FakeProvider(market)
    worker = _FakeWorker()
    events = _FakeEventBridge()
    ctx = ViewModelContext(provider=provider, worker=worker, events=events, session_id="s1")
    vm = MarketViewModel(ctx)
    return vm, worker, market, events


class TestConstructionDoesNotLoadOptionChain:
    """MarketViewModel construction must not dispatch a broker REST call."""

    def test_no_worker_dispatch_on_construction(self, qapp: QApplication) -> None:
        vm, worker, market, events = _make_viewmodel(qapp)

        assert worker.calls == []
        assert market.initial_option_chain_calls == []


class TestBrokerConnectedTriggersSingleLoad:
    def test_broker_connected_triggers_exactly_one_load(self, qapp: QApplication) -> None:
        vm, worker, market, events = _make_viewmodel(qapp)

        events.broker_connected.emit({"broker": "breeze"})

        assert len(worker.calls) == 1
        worker.execute()
        assert len(market.initial_option_chain_calls) == 1
        assert market.initial_option_chain_calls[0] == ("s1", "NIFTY", "NFO", 10)

    def test_repeated_broker_connected_does_not_duplicate_load(self, qapp: QApplication) -> None:
        vm, worker, market, events = _make_viewmodel(qapp)

        events.broker_connected.emit({"broker": "breeze"})
        events.broker_connected.emit({"broker": "breeze"})
        events.broker_connected.emit({"broker": "breeze"})

        assert len(worker.calls) == 1


class TestAuthenticationSucceededDoesNotDuplicate:
    def test_authentication_succeeded_after_broker_connected_is_a_noop(
        self, qapp: QApplication
    ) -> None:
        vm, worker, market, events = _make_viewmodel(qapp)

        events.broker_connected.emit({"broker": "breeze"})
        events.authentication_succeeded.emit({"broker": "breeze"})

        assert len(worker.calls) == 1

    def test_authentication_succeeded_before_broker_connected_still_triggers_once(
        self, qapp: QApplication
    ) -> None:
        vm, worker, market, events = _make_viewmodel(qapp)

        events.authentication_succeeded.emit({"broker": "breeze"})
        events.broker_connected.emit({"broker": "breeze"})

        assert len(worker.calls) == 1


class TestReconnectAfterDisconnectReloads:
    def test_broker_disconnected_then_reconnected_triggers_a_fresh_load(
        self, qapp: QApplication
    ) -> None:
        vm, worker, market, events = _make_viewmodel(qapp)

        events.broker_connected.emit({"broker": "breeze"})
        events.broker_disconnected.emit({"broker": "breeze"})
        events.broker_connected.emit({"broker": "breeze"})

        assert len(worker.calls) == 2


class TestExplicitLoadOptionChainStillWorks:
    def test_explicit_call_after_connected_dispatches_again(self, qapp: QApplication) -> None:
        vm, worker, market, events = _make_viewmodel(qapp)
        events.broker_connected.emit({"broker": "breeze"})
        assert len(worker.calls) == 1

        vm.load_option_chain("BANKNIFTY", exchange="NFO")

        assert len(worker.calls) == 2
        worker.execute()
        assert market.initial_option_chain_calls[-1] == ("s1", "BANKNIFTY", "NFO", 10)

    def test_explicit_call_before_any_connection_is_skipped(self, qapp: QApplication) -> None:
        vm, worker, market, events = _make_viewmodel(qapp)

        vm.load_option_chain()

        assert worker.calls == []
        assert market.initial_option_chain_calls == []


class TestChainWidthToggle:
    """set_chain_width() controls the window_radius passed to initial_option_chain()."""

    def test_default_width_is_ten(self, qapp: QApplication) -> None:
        vm, worker, market, events = _make_viewmodel(qapp)
        events.broker_connected.emit({"broker": "breeze"})
        worker.execute()

        assert market.initial_option_chain_calls[0] == ("s1", "NIFTY", "NFO", 10)

    def test_changing_width_before_connection_is_stored_but_does_not_dispatch(
        self, qapp: QApplication
    ) -> None:
        vm, worker, market, events = _make_viewmodel(qapp)

        vm.set_chain_width(20)

        assert worker.calls == []
        assert market.initial_option_chain_calls == []

    def test_changing_width_after_connection_reloads_with_new_radius(
        self, qapp: QApplication
    ) -> None:
        vm, worker, market, events = _make_viewmodel(qapp)
        events.broker_connected.emit({"broker": "breeze"})
        worker.execute()

        vm.set_chain_width(20)

        assert len(worker.calls) == 2
        worker.execute()
        assert market.initial_option_chain_calls[-1] == ("s1", "NIFTY", "NFO", 20)

    def test_setting_same_width_is_a_noop(self, qapp: QApplication) -> None:
        vm, worker, market, events = _make_viewmodel(qapp)
        events.broker_connected.emit({"broker": "breeze"})
        worker.execute()

        vm.set_chain_width(10)

        assert len(worker.calls) == 1

    def test_deferred_width_change_is_used_by_the_next_connection(
        self, qapp: QApplication
    ) -> None:
        vm, worker, market, events = _make_viewmodel(qapp)

        vm.set_chain_width(30)
        events.broker_connected.emit({"broker": "breeze"})
        worker.execute()

        assert market.initial_option_chain_calls[0] == ("s1", "NIFTY", "NFO", 30)
