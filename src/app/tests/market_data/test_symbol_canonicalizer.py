"""Tests for broker-symbol canonicalization before tick dispatch."""

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.market_data.symbols import (
    InstrumentMasterSymbolCanonicalizer,
    build_option_contract_symbol,
)
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


class _RealisticInstrumentMaster:
    """Instrument Master double mirroring the app's seeded index display names.

    FINNIFTY and MIDCPNIFTY are deliberately seeded with their full display
    names ("NIFTY Financial Services", "NIFTY Midcap Select") which do not
    match Breeze's abbreviated feed labels ("NIFTY FIN SERVICE",
    "NIFTY MID SELECT"), reproducing the real-world mismatch the alias map
    resolves.
    """

    _BY_DISPLAY_NAME = {
        "nifty 50": "NIFTY",
        "nifty bank": "BANKNIFTY",
        "nifty financial services": "FINNIFTY",
        "nifty midcap select": "MIDCPNIFTY",
    }

    def find_by_symbol(self, symbol: str) -> list[object]:
        return []

    def find_by_display_name(self, display_name: str) -> list[object]:
        trading_symbol = self._BY_DISPLAY_NAME.get(display_name.casefold().strip())
        if trading_symbol is None:
            return []
        return [SimpleNamespace(trading_symbol=trading_symbol)]

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


class TestIndexDisplayNameCanonicalization:
    """Breeze index display names resolve to the application's canonical symbols."""

    def test_nifty_50_resolves_via_instrument_master(self) -> None:
        resolver = InstrumentMasterSymbolCanonicalizer(_RealisticInstrumentMaster())

        canonical = resolver.canonicalize("NIFTY 50", exchange="NSE")

        assert canonical.symbol == "NIFTY"

    def test_nifty_bank_resolves_via_instrument_master(self) -> None:
        resolver = InstrumentMasterSymbolCanonicalizer(_RealisticInstrumentMaster())

        canonical = resolver.canonicalize("NIFTY BANK", exchange="NSE")

        assert canonical.symbol == "BANKNIFTY"

    def test_nifty_fin_service_resolves_via_alias(self) -> None:
        resolver = InstrumentMasterSymbolCanonicalizer(_RealisticInstrumentMaster())

        canonical = resolver.canonicalize("NIFTY FIN SERVICE", exchange="NSE")

        assert canonical.symbol == "FINNIFTY"
        assert canonical.broker_symbol == "NIFTY FIN SERVICE"

    def test_nifty_mid_select_resolves_via_alias(self) -> None:
        resolver = InstrumentMasterSymbolCanonicalizer(_RealisticInstrumentMaster())

        canonical = resolver.canonicalize("NIFTY MID SELECT", exchange="NSE")

        assert canonical.symbol == "MIDCPNIFTY"
        assert canonical.broker_symbol == "NIFTY MID SELECT"

    def test_alias_resolution_is_case_insensitive(self) -> None:
        resolver = InstrumentMasterSymbolCanonicalizer(_RealisticInstrumentMaster())

        lower = resolver.canonicalize("nifty fin service", exchange="NSE")
        mixed = resolver.canonicalize("Nifty Mid Select", exchange="NSE")

        assert lower.symbol == "FINNIFTY"
        assert mixed.symbol == "MIDCPNIFTY"

    def test_alias_resolution_strips_token_prefix(self) -> None:
        resolver = InstrumentMasterSymbolCanonicalizer(_RealisticInstrumentMaster())

        canonical = resolver.canonicalize("4.1!NIFTY FIN SERVICE", exchange="NSE")

        assert canonical.symbol == "FINNIFTY"
        assert canonical.broker_symbol == "4.1!NIFTY FIN SERVICE"

    def test_unrelated_symbol_is_not_mapped(self) -> None:
        resolver = InstrumentMasterSymbolCanonicalizer(_RealisticInstrumentMaster())

        canonical = resolver.canonicalize("RELIANCE", exchange="NSE")

        assert canonical.symbol == "RELIANCE"

    def test_unrelated_symbol_with_no_instrument_master_is_not_mapped(self) -> None:
        resolver = InstrumentMasterSymbolCanonicalizer(None)

        canonical = resolver.canonicalize("SOME OTHER STOCK", exchange="NSE")

        assert canonical.symbol == "SOME OTHER STOCK"


class TestBuildOptionContractSymbol:
    """Deterministic canonical option contract symbol construction."""

    def test_call_contract_symbol(self) -> None:
        symbol = build_option_contract_symbol("NIFTY", "13-Feb-2026", "24500", "Call")

        assert symbol == "NIFTY-13-Feb-2026-24500-CE"

    def test_put_contract_symbol(self) -> None:
        symbol = build_option_contract_symbol("NIFTY", "13-Feb-2026", "24500", "Put")

        assert symbol == "NIFTY-13-Feb-2026-24500-PE"

    def test_ce_pe_broker_right_values_accepted(self) -> None:
        assert build_option_contract_symbol("NIFTY", "13-Feb-2026", "24500", "CE") == (
            "NIFTY-13-Feb-2026-24500-CE"
        )
        assert build_option_contract_symbol("NIFTY", "13-Feb-2026", "24500", "PE") == (
            "NIFTY-13-Feb-2026-24500-PE"
        )

    def test_strike_without_trailing_zero(self) -> None:
        symbol = build_option_contract_symbol("NIFTY", "13-Feb-2026", "24500.0", "CE")

        assert symbol == "NIFTY-13-Feb-2026-24500-CE"

    def test_fractional_strike_is_preserved(self) -> None:
        symbol = build_option_contract_symbol("NIFTY", "13-Feb-2026", "24550.5", "PE")

        assert symbol == "NIFTY-13-Feb-2026-24550.5-PE"
