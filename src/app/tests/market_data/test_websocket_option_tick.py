"""Tests for option tick canonical-symbol construction in WebSocketService.

Confirms option ticks get a deterministic contract symbol
(underlying-expiry-strike-side) while the raw broker token is preserved as
broker_symbol, and that this leaves the already-working cash-index tick
canonicalization path untouched.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.market_data.symbols import InstrumentMasterSymbolCanonicalizer
from app.market_data.websocket.websocket_service import WebSocketService


class _InstrumentMaster:
    """Instrument Master double resolving Breeze's NIFTY display name."""

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


def test_option_tick_canonical_symbol_contains_underlying_expiry_strike_side() -> None:
    service, dispatcher = _service()

    service._process_tick(
        {
            "stock_code": "4.1!51219",
            "stock_name": "4.1!NIFTY 50",
            "exchange_code": "NFO",
            "expiry_date": "13-Feb-2026",
            "strike_price": "24500",
            "right": "Call",
            "product_type": "options",
            "ltp": "120.5",
        }
    )

    tick = dispatcher.enqueue.call_args.args[0]
    assert tick.symbol == "NIFTY-13-Feb-2026-24500-CE"


def test_option_tick_retains_raw_broker_token_as_broker_symbol() -> None:
    service, dispatcher = _service()

    service._process_tick(
        {
            "stock_code": "4.1!51219",
            "stock_name": "4.1!NIFTY 50",
            "exchange_code": "NFO",
            "expiry_date": "13-Feb-2026",
            "strike_price": "24500",
            "right": "Put",
            "product_type": "options",
            "ltp": "80.25",
        }
    )

    tick = dispatcher.enqueue.call_args.args[0]
    assert tick.broker_symbol == "4.1!51219"
    assert tick.symbol == "NIFTY-13-Feb-2026-24500-PE"


def test_option_tick_underlying_resolved_via_instrument_master_stock_name() -> None:
    """Underlying resolution must go through InstrumentMasterSymbolCanonicalizer."""
    service, dispatcher = _service()

    service._process_tick(
        {
            "stock_code": "4.1!99999",
            "stock_name": "Unmapped Display Name",
            "exchange_code": "NFO",
            "expiry_date": "13-Feb-2026",
            "strike_price": "100",
            "right": "Call",
            "product_type": "options",
            "ltp": "1.5",
        }
    )

    tick = dispatcher.enqueue.call_args.args[0]
    # Underlying falls back to the raw (unmatched) display name, never a raw token guess.
    assert tick.symbol == "Unmapped Display Name-13-Feb-2026-100-CE"


class TestCashIndexTickRegression:
    """Cash-index ticks must keep resolving through the existing plain path."""

    def test_nifty_cash_tick_still_canonicalizes_via_instrument_master(self) -> None:
        service, dispatcher = _service()

        service._process_tick(
            {"stock_code": "4.1!NIFTY 50", "exchange_code": "NSE", "ltp": "24502.1"}
        )

        tick = dispatcher.enqueue.call_args.args[0]
        assert tick.symbol == "NIFTY"
        assert tick.broker_symbol == "4.1!NIFTY 50"

    def test_banknifty_cash_tick_is_not_treated_as_option_tick(self) -> None:
        service, dispatcher = _service()

        service._process_tick(
            {"stock_code": "BANKNIFTY", "exchange_code": "NSE", "ltp": "51000"}
        )

        tick = dispatcher.enqueue.call_args.args[0]
        assert tick.symbol == "BANKNIFTY"
        assert tick.option_right == ""
        assert tick.strike_price == ""
