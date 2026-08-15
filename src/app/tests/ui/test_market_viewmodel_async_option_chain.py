"""Async, cross-thread regression tests for the option-chain UI delivery path.

Task 13: proves the real path

    MarketViewModel -> BackgroundWorker -> QThreadPool -> work completes
    -> result delivered on the GUI thread -> done() -> option_chain_changed
    -> OptionChainView.load_rows() -> table model row count

genuinely crosses the worker-thread boundary via a REAL BackgroundWorker
(not a synchronous fake), which is exactly the gap the previously-existing
end-to-end pipeline test (test_option_chain_pipeline_end_to_end.py) does not
cover -- that test explicitly runs BackgroundWorker's callback synchronously
in-thread by design, so it could not have caught the silent cross-thread
delivery failure this task fixes.
"""

import time

import pytest
from PySide6.QtCore import QCoreApplication, QObject, Signal
from PySide6.QtWidgets import QApplication

from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult
from app.ui.application.worker_pool import BackgroundWorker
from app.ui.market.market_view import MarketView
from app.ui.option_chain.option_chain_view import OptionChainView
from app.ui.viewmodels.context import ViewModelContext
from app.ui.viewmodels.market_viewmodel import MarketViewModel

_STRIKES = [str(24350 + offset * 50) for offset in range(-10, 11)]  # 21 strikes, ATM=24350


def _realistic_strikes() -> list[dict]:
    """Shape matching OptionStrike.model_dump(mode="json") field names."""
    rows = []
    for index, strike in enumerate(_STRIKES):
        rows.append(
            {
                "strike_price": strike,
                "expiry_date": "18-Aug-2026",
                "call_symbol": f"NIFTY18AUG26{strike}CE",
                "put_symbol": f"NIFTY18AUG26{strike}PE",
                "call_ltp": str(100.0 - index),
                "put_ltp": str(50.0 + index),
                "call_oi": 40000 + index * 100,
                "put_oi": 35000 + index * 100,
                "call_volume": 90000 + index * 10,
                "put_volume": 70000 + index * 10,
                "call_iv": None,
                "put_iv": None,
                "is_atm": strike == "24350",
            }
        )
    return rows


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
    """MarketWorkspaceService double returning a realistic 21-strike result,
    matching the live-confirmed shape (Task 12 investigation): CALL+PUT
    fetched, merged, ATM-windowed to 21 strikes, success=True."""

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

    def initial_option_chain(
        self, session_id: str, underlying: str = "NIFTY", *, exchange: str = "NFO"
    ) -> WorkspaceOperationResult:
        self.initial_option_chain_calls.append((session_id, underlying, exchange))
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            f"Option chain for {underlying} 18-Aug-2026 (21 strikes)",
            {
                "underlying": underlying,
                "exchange": exchange,
                "expiry_date": "18-Aug-2026",
                "spot_price": "24336.6",
                "atm_strike": "24350",
                "strikes": _realistic_strikes(),
            },
        )


class _FakeProvider:
    def __init__(self, market: _FakeMarketService) -> None:
        self.market = market


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _pump_until(predicate, timeout: float = 5.0) -> bool:
    """See test_worker_pool_thread_marshaling.py for rationale: this drains
    the Qt event loop so queued cross-thread deliveries actually happen."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QCoreApplication.processEvents()
        if predicate():
            return True
        time.sleep(0.01)
    return False


@pytest.fixture
def real_async_pipeline(qapp: QApplication):
    """MarketViewModel wired to a REAL BackgroundWorker/QThreadPool."""
    market = _FakeMarketService()
    provider = _FakeProvider(market)
    worker = BackgroundWorker()
    events = _FakeEventBridge()
    ctx = ViewModelContext(provider=provider, worker=worker, events=events, session_id="async-1")
    vm = MarketViewModel(ctx)
    return vm, market, events


class TestOptionChainChangedEmittedAcrossRealWorkerThread:
    """Test 3."""

    def test_broker_connected_triggers_async_load_that_reaches_option_chain_changed(
        self, real_async_pipeline
    ) -> None:
        vm, market, events = real_async_pipeline
        emitted_rows: list[list[tuple]] = []
        vm.option_chain_changed.connect(emitted_rows.append)

        events.broker_connected.emit({"broker": "breeze"})

        assert _pump_until(lambda: len(emitted_rows) == 1), (
            "option_chain_changed was never emitted -- the async worker-thread "
            "-> GUI-thread delivery is broken (this is the Task 12 root cause)"
        )
        assert len(market.initial_option_chain_calls) == 1

        rows = emitted_rows[0]
        assert len(rows) == len(_STRIKES) * 2  # one CE + one PE row per strike
        ce_rows = [row for row in rows if row[0] == "CE"]
        pe_rows = [row for row in rows if row[0] == "PE"]
        assert len(ce_rows) == 21
        assert len(pe_rows) == 21


class TestOptionChainViewReceivesRowsAcrossRealWorkerThread:
    """Test 4."""

    def test_option_chain_table_model_populated_after_async_load(
        self, real_async_pipeline
    ) -> None:
        vm, market, events = real_async_pipeline
        view = MarketView(vm)
        chain_view: OptionChainView = view._chain  # noqa: SLF001 - test introspection

        assert chain_view._model.rowCount() == 0  # noqa: SLF001

        events.broker_connected.emit({"broker": "breeze"})

        assert _pump_until(lambda: chain_view._model.rowCount() > 0, timeout=5.0), (  # noqa: SLF001
            "OptionChainView table model never received rows from the async load"
        )

        assert chain_view._model.rowCount() == 42  # noqa: SLF001
        assert chain_view._model.columnCount() == 9  # noqa: SLF001
