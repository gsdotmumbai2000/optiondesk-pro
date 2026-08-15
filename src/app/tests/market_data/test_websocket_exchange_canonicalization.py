"""Regression coverage for raw Breeze exchange label canonicalization in
WebSocketService._process_tick().

Breeze's raw tick payloads carry human-readable exchange labels ("NSE
Equity", "NSE Futures & Options") rather than the application's canonical
exchange codes ("NSE", "NFO"). Every downstream consumer (LiveTickCache keys,
ChainKey, the calculation context, get_spot()) assumes canonical codes, so an
uncanonicalized label breaks any lookup that crosses from one tick's cache
entry to another (e.g. a spot lookup keyed by the option chain's exchange).
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.market_data.symbols import InstrumentMasterSymbolCanonicalizer
from app.market_data.websocket.websocket_service import WebSocketService


class _InstrumentMaster:
    def find_by_symbol(self, symbol: str) -> list[object]:
        return []

    def find_by_display_name(self, display_name: str) -> list[object]:
        if display_name.casefold().strip() == "nifty 50":
            return [SimpleNamespace(trading_symbol="NIFTY")]
        return []

    def find_by_broker_symbol(self, broker_code: str, broker_symbol: str) -> list[object]:
        return []


def _service() -> tuple[WebSocketService, MagicMock]:
    dispatcher = MagicMock()
    service = WebSocketService(
        MagicMock(),
        dispatcher,
        symbol_canonicalizer=InstrumentMasterSymbolCanonicalizer(_InstrumentMaster()),
    )
    return service, dispatcher


def test_cash_tick_raw_nse_equity_label_is_canonicalized_to_nse() -> None:
    service, dispatcher = _service()

    service._process_tick(
        {"symbol": "4.1!NIFTY 50", "exchange": "NSE Equity", "stock_name": "NIFTY 50", "last": "24380.55"}
    )

    tick = dispatcher.enqueue.call_args.args[0]
    assert tick.symbol == "NIFTY"
    assert tick.exchange == "NSE"


def test_option_tick_raw_nse_futures_and_options_label_is_canonicalized_to_nfo() -> None:
    service, dispatcher = _service()

    service._process_tick(
        {
            "symbol": "4.1!45080",
            "exchange": "NSE Futures & Options",
            "product_type": "Options",
            "stock_name": "NIFTY 50",
            "strike_price": "23850",
            "right": "Call",
            "expiry_date": "18-Aug-2026",
            "ltp": "580",
        }
    )

    tick = dispatcher.enqueue.call_args.args[0]
    assert tick.symbol == "NIFTY-18-Aug-2026-23850-CE"
    assert tick.exchange == "NFO"


def test_already_canonical_exchange_code_is_left_unchanged() -> None:
    service, dispatcher = _service()

    service._process_tick({"stock_code": "BANKNIFTY", "exchange_code": "NSE", "ltp": "51000"})

    tick = dispatcher.enqueue.call_args.args[0]
    assert tick.exchange == "NSE"
