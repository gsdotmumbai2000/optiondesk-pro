"""Tests for broker-symbol canonicalization before tick dispatch."""

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.market_data.symbols import InstrumentMasterSymbolCanonicalizer
from app.market_data.websocket.websocket_service import WebSocketService


class _InstrumentMaster:
    """Minimal Instrument Master double used by the canonicalizer."""

    def find_by_symbol(self, symbol: str) -> list[object]:
        return []

    def find_by_display_name(self, display_name: str) -> list[object]:
        if display_name == "NIFTY 50":
            return [SimpleNamespace(trading_symbol="NIFTY")]
        return []

    def find_by_broker_symbol(
        self, broker_code: str, broker_symbol: str
    ) -> list[object]:
        return []


def test_resolves_broker_feed_label_through_instrument_master() -> None:
    resolver = InstrumentMasterSymbolCanonicalizer(_InstrumentMaster())

    canonical = resolver.canonicalize("4.1!NIFTY 50", exchange="NSE")

    assert canonical.symbol == "NIFTY"
    assert canonical.broker_symbol == "4.1!NIFTY 50"


def test_tick_uses_canonical_symbol_and_retains_broker_symbol() -> None:
    dispatcher = MagicMock()
    service = WebSocketService(
        MagicMock(),
        dispatcher,
        symbol_canonicalizer=InstrumentMasterSymbolCanonicalizer(
            _InstrumentMaster()
        ),
    )

    service._process_tick(
        {
            "stock_code": "4.1!NIFTY 50",
            "exchange_code": "NSE",
            "ltp": "25000",
            "change": "10",
        }
    )

    tick = dispatcher.enqueue.call_args.args[0]
    assert tick.symbol == "NIFTY"
    assert tick.broker_symbol == "4.1!NIFTY 50"
    assert tick.ltp == Decimal("25000")
