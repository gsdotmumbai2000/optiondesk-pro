"""OFFLINE end-to-end verification of the Option Chain pipeline.

This is deterministic, mocked verification using a fake Breeze SDK client —
NOT a live-market test. It exercises the real production wiring across every
layer between the fake SDK boundary and the UI signal boundary:

    MarketViewModel.load_option_chain()
        -> MarketWorkspaceService.initial_option_chain()   (real)
        -> MarketDataQueryService.get_option_chain()        (real)
        -> BreezeBrokerAdapter.get_option_chain()            (real, connected)
        -> BreezeOptionChain.get_option_chain()              (real)
        -> CALL + PUT requests to the fake Breeze SDK client
        -> unwrap_success()                                  (real, fixed)
        -> normalize_option_chain() (breeze-level)            (real)
        -> normalize_option_chain() (market-data-level)       (real)
        -> ATM-window slicing + subscription requests         (real)
        -> MarketViewModel.option_chain_changed                (real)

Only the outermost boundaries are faked: the Breeze SDK client itself
(no network), and the BackgroundWorker (runs synchronously instead of on a
QThreadPool thread, so assertions don't need to wait on Qt signals).

Steps already covered by dedicated, more granular tests are NOT
re-verified here in detail — see test_breeze_option_chain_normalizer.py
(CALL/PUT merge, ordering, IV, LTP/OI/Volume field mapping),
test_subscription_service.py (CALL/PUT subscription key collision),
test_websocket_option_tick.py (option tick canonical symbols, cash-index
regression), and test_market_workspace_expiry.py (ATM-window size, expiry
resolution). This test's job is to prove those pieces are wired together
correctly end-to-end, not to re-derive their unit-level correctness.
"""

import types
from datetime import date, datetime

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.services.market_workspace_service import MarketWorkspaceService
from app.brokers.bootstrap import BrokerProvider
from app.brokers.shared.enums import ProductType
from app.config.models.app_config import BrokerConfig
from app.events.event_bus import EventBus
from app.market.bootstrap import MarketMasterProvider
from app.market.enums import ExpiryType
from app.market_data.cache.market_cache import MarketCache
from app.market_data.history.history_manager import HistoryManager
from app.market_data.models.live_status import LiveMarketStatus, MarketStatusSnapshot
from app.market_data.services.query_service import MarketDataQueryService
from app.market_data.snapshots.snapshot_manager import SnapshotManager
from app.market_data.validation.validators import MarketDataValidator
from app.market_data.websocket.connection_state import MarketDataConnectionState
from app.security.credential_manager import CredentialManager
from app.tests.brokers.conftest import MockBreezeClient
from app.ui.viewmodels.context import ViewModelContext
from app.ui.viewmodels.market_viewmodel import MarketViewModel

_STRIKES = ["24400", "24450", "24500", "24550", "24600"]


def _rows_for_right(right: str) -> list[dict]:
    """Realistic-looking NIFTY 18-Aug-2026 CALL/PUT rows around ATM 24500."""
    is_call = right == "call"
    rows = []
    for index, strike in enumerate(_STRIKES):
        ltp = 180.0 - index * 30.0 if is_call else 60.0 + index * 30.0
        oi = 40000 + index * 1000 if is_call else 35000 + index * 1000
        volume = 90000 + index * 500 if is_call else 70000 + index * 500
        rows.append(
            {
                "strike_price": strike,
                "right": right,
                "stock_code": f"NIFTY18AUG26{strike}{'CE' if is_call else 'PE'}",
                "ltp": str(ltp),
                "best_bid_price": str(ltp - 1),
                "best_offer_price": str(ltp + 1),
                "open_interest": str(oi),
                "total_quantity_traded": str(volume),
                "spot_price": "24523",
                # No implied_volatility field — Breeze's option-chain quotes
                # payload does not provide it; must not be invented.
            }
        )
    return rows


class _RealisticOptionChainClient(MockBreezeClient):
    """Extends the shared MockBreezeClient with a realistic
    get_option_chain_quotes() implementation returning Breeze's confirmed
    live envelope: {"Success": [...], "Status": 200, "Error": None}."""

    def __init__(self, api_key: str) -> None:
        super().__init__(api_key)
        self.option_chain_calls: list[dict] = []

    def get_option_chain_quotes(self, **kwargs) -> dict:
        self.option_chain_calls.append(dict(kwargs))
        return {
            "Success": _rows_for_right(kwargs.get("right", "")),
            "Status": 200,
            "Error": None,
        }


class _MarketDataServiceAdapter:
    """Thin adapter exposing only the MarketDataService surface that
    MarketWorkspaceService.initial_option_chain() needs, backed by a REAL
    MarketDataQueryService (itself backed by the real, connected
    BreezeBrokerAdapter) rather than canned data."""

    def __init__(self, query_service: MarketDataQueryService) -> None:
        self._query = query_service
        self.subscribe_calls: list[dict] = []

    def get_option_chain(self, underlying: str, exchange: str, expiry_date: str):
        return self._query.get_option_chain(underlying, exchange, expiry_date)

    def latest_tick(self, symbol: str, exchange: str):
        return None

    def load_watchlist(self, symbols: tuple[str, ...]) -> None:
        """No-op: MarketViewModel construction loads the watchlist, which
        this pipeline test does not exercise beyond not crashing."""
        return None

    def market_status(self) -> MarketStatusSnapshot:
        return MarketStatusSnapshot(
            status=LiveMarketStatus.CLOSED, exchange="NSE", trade_date="2026-08-12"
        )

    def connection_status(self) -> MarketDataConnectionState:
        return MarketDataConnectionState.DISCONNECTED

    def last_tick_time(self):
        return None

    def subscribe(
        self,
        underlying: str,
        exchange: str,
        *,
        product_type: ProductType,
        expiry_date: str = "",
        strike_price: str = "",
        option_right: str = "",
    ) -> None:
        self.subscribe_calls.append(
            {
                "underlying": underlying,
                "exchange": exchange,
                "product_type": product_type,
                "expiry_date": expiry_date,
                "strike_price": strike_price,
                "option_right": option_right,
            }
        )


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


class _FakeWorker:
    """BackgroundWorker double: records dispatches, runs them synchronously on demand."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def run(self, fn, on_finished, on_error) -> None:
        self.calls.append((fn, on_finished, on_error))

    def execute(self, index: int = -1) -> None:
        fn, done, err = self.calls[index]
        try:
            result = fn()
        except Exception as exc:  # noqa: BLE001
            err(str(exc))
            return
        done(result)


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


@pytest.fixture
def pipeline(qapp: QApplication, tmp_path):
    """Wire the full offline pipeline: fake Breeze SDK -> real broker/market-data
    services -> real MarketWorkspaceService -> real MarketViewModel."""
    broker_config = BrokerConfig(
        broker_code="BREEZE",
        account_name="Default",
        websocket_enabled=False,
        auto_login=True,
    )
    credential_manager = CredentialManager()
    credential_manager.store_api_key("Default", "test-api-key")
    credential_manager.store_api_secret("Default", "test-secret")
    credential_manager.store_session_token("Default", "test-session")

    event_bus = EventBus()
    broker_provider = BrokerProvider(
        broker_config,
        credential_manager,
        event_bus,
        client_factory=lambda api_key: _RealisticOptionChainClient(api_key),
    )
    broker_provider.manager.connect()
    assert broker_provider.broker_service.is_connected()
    breeze_client: _RealisticOptionChainClient = broker_provider.broker_service._client

    query_service = MarketDataQueryService(
        broker_provider.broker_service,
        MarketCache(),
        HistoryManager(),
        SnapshotManager(),
        MarketDataValidator(),
    )
    market_data_adapter = _MarketDataServiceAdapter(query_service)

    market_master = MarketMasterProvider(tmp_path, EventBus())
    engines = types.SimpleNamespace(market_master=market_master)
    market_workspace = MarketWorkspaceService(
        engines, None, WorkspaceCache(), market_data=market_data_adapter
    )

    vm_provider = types.SimpleNamespace(market=market_workspace)
    worker = _FakeWorker()
    events = _FakeEventBridge()
    ctx = ViewModelContext(provider=vm_provider, worker=worker, events=events, session_id="e2e")
    vm = MarketViewModel(ctx)

    yield types.SimpleNamespace(
        vm=vm,
        worker=worker,
        events=events,
        breeze_client=breeze_client,
        market_data_adapter=market_data_adapter,
        market_master=market_master,
    )
    market_master.shutdown()
    broker_provider.stop()


class TestOptionChainPipelineEndToEnd:
    def test_full_pipeline_produces_populated_option_chain_changed(self, pipeline) -> None:
        emitted_rows: list[list[tuple]] = []
        pipeline.vm.option_chain_changed.connect(emitted_rows.append)

        # Real auto-trigger path: broker_connected -> MarketViewModel._on_broker_ready
        # -> load_option_chain() (item 3: request dispatched via the real gating logic).
        pipeline.events.broker_connected.emit({"broker": "breeze"})
        assert len(pipeline.worker.calls) == 1  # exactly one auto-triggered load
        pipeline.worker.execute()

        # --- B: CALL and PUT request counts ---
        assert [c["right"] for c in pipeline.breeze_client.option_chain_calls] == ["call", "put"]
        assert len(pipeline.breeze_client.option_chain_calls) == 2

        # Requests reached the real Breeze SDK boundary with NFO/NIFTY/ISO expiry.
        # The expiry is resolved dynamically (never hardcoded in production),
        # so compute the expected value the same way rather than assuming a
        # fixed date — at the time this suite was authored it resolves to
        # 18-Aug-2026, matching the confirmed live evidence.
        expiry_record = pipeline.market_master.expiry_service.nearest_expiry(
            "NIFTY", "NSEFO", on_date=date.today()
        )
        expected_expiry_iso = datetime.strptime(
            expiry_record.expiry_date.strftime("%d-%b-%Y"), "%d-%b-%Y"
        ).strftime("%Y-%m-%dT06:00:00.000Z")
        for call in pipeline.breeze_client.option_chain_calls:
            assert call["stock_code"] == "NIFTY"
            assert call["exchange_code"] == "NFO"
            assert call["expiry_date"] == expected_expiry_iso
            assert call["strike_price"] == ""

        # --- 12: no exception anywhere in the pipeline ---
        # (worker.execute() would have routed to err() instead of done() —
        # confirm done() path fired by checking the signal below.)

        # --- 13/E: option_chain_changed emitted with populated rows ---
        assert len(emitted_rows) == 1
        rows = emitted_rows[0]
        assert rows  # populated, not empty

        # --- C: strike count / D: CE+PE row counts ---
        assert len(rows) == len(_STRIKES) * 2  # one CE + one PE row per strike
        ce_rows = [row for row in rows if row[0] == "CE"]
        pe_rows = [row for row in rows if row[0] == "PE"]
        assert len(ce_rows) == len(_STRIKES)
        assert len(pe_rows) == len(_STRIKES)

        # --- 7: strike ordering preserved ascending ---
        assert [row[1] for row in ce_rows] == _STRIKES

        # --- 8/9: CALL/PUT LTP-derived OI and volume preserved through the
        # full pipeline (row tuple = side, strike, ltp, oi, volume, iv, ...) ---
        atm_call = next(row for row in ce_rows if row[1] == "24500")
        atm_put = next(row for row in pe_rows if row[1] == "24500")
        assert atm_call[2] == "120.0"  # call LTP (180.0 - 2*30.0)
        assert atm_put[2] == "120.0"  # put LTP (60.0 + 2*30.0)
        assert atm_call[3] == "42000"  # call_oi at index 3 (40000 + 2*1000)
        assert atm_call[4] == "91000"  # call_volume (90000 + 2*500)
        assert atm_put[3] == "37000"  # put_oi (35000 + 2*1000)
        assert atm_put[4] == "71000"  # put_volume (70000 + 2*500)

        # --- 15: IV/Greeks solved locally from LTP + spot when Breeze's
        # payload carries neither (see app.calculation.utilities.leg_greeks) ---
        for row in rows:
            iv, delta, gamma, theta, vega = row[5:]
            assert iv != "—"
            assert delta != "—"
            assert gamma != "—"
            assert theta != "—"
            assert vega != "—"
        atm_call_delta = float(atm_call[6])
        atm_put_delta = float(atm_put[6])
        assert 0.0 < atm_call_delta < 1.0  # ATM call delta is positive
        assert -1.0 < atm_put_delta < 0.0  # ATM put delta is negative

        # --- 5: no CALL/PUT subscription-key collision — distinct
        # (strike_price, option_right) pairs for every OPTIONS subscribe()
        # call. initial_option_chain() subscribes the *full* +/-10-interval
        # ATM window (21 strikes), independent of how many of those strikes
        # had REST data in this response — this is existing, correct
        # production behavior (verified separately by
        # test_market_workspace_expiry.py and test_subscription_service.py),
        # not something this test re-derives; here we only confirm every
        # (strike, right) pair reaching the subscription boundary is unique. ---
        option_calls = [
            call for call in pipeline.market_data_adapter.subscribe_calls
            if call["product_type"] == ProductType.OPTIONS
        ]
        keys = [(call["strike_price"], call["option_right"]) for call in option_calls]
        assert len(keys) == 21 * 2
        assert len(set(keys)) == len(keys)  # every key unique, no collisions
        assert {right for _, right in keys} == {"CALL", "PUT"}
        # And every strike that actually had REST data is among the
        # subscribed strikes (both sides).
        for strike in _STRIKES:
            assert (strike, "CALL") in keys
            assert (strike, "PUT") in keys

        # --- futures: initial_option_chain() also subscribes exactly one
        # NIFTY/NFO future, at its own dynamically-resolved *monthly*
        # expiry (Task 9 subscribes it; Task 10 fixes which expiry it uses
        # -- NIFTY futures are monthly, options are weekly, so this must
        # differ from the option chain's weekly expiry_record above). ---
        future_calls = [
            call for call in pipeline.market_data_adapter.subscribe_calls
            if call["product_type"] == ProductType.FUTURES
        ]
        assert len(future_calls) == 1
        assert future_calls[0]["underlying"] == "NIFTY"
        assert future_calls[0]["exchange"] == "NFO"
        future_expiry_record = pipeline.market_master.expiry_service.nearest_expiry(
            "NIFTY", "NSEFO", on_date=date.today(), expiry_type=ExpiryType.MONTHLY
        )
        assert future_calls[0]["expiry_date"] == future_expiry_record.expiry_date.strftime("%d-%b-%Y")
        assert future_calls[0]["expiry_date"] != expiry_record.expiry_date.strftime("%d-%b-%Y")
        assert future_calls[0]["strike_price"] == ""
        assert future_calls[0]["option_right"] == ""

    def test_authentication_succeeded_does_not_duplicate_the_auto_triggered_load(
        self, pipeline
    ) -> None:
        pipeline.events.broker_connected.emit({"broker": "breeze"})
        pipeline.events.authentication_succeeded.emit({"broker": "breeze"})

        assert len(pipeline.worker.calls) == 1
