"""Tests for UnderlyingProvider and cash_exchange_for()."""

from app.calculation.providers.underlying_provider import (
    UnderlyingProvider,
    cash_exchange_for,
)


def test_underlying_provider_resolve_uppercases_symbol_and_exchange() -> None:
    info = UnderlyingProvider().resolve("nifty", "nfo")

    assert info.underlying == "NIFTY"
    assert info.underlying_symbol == "NIFTY"
    assert info.exchange == "NFO"
    assert info.currency == "INR"


def test_cash_exchange_for_nfo_is_nse() -> None:
    assert cash_exchange_for("NFO") == "NSE"


def test_cash_exchange_for_bfo_is_bse() -> None:
    assert cash_exchange_for("BFO") == "BSE"


def test_cash_exchange_for_is_case_insensitive() -> None:
    assert cash_exchange_for("nfo") == "NSE"


def test_cash_exchange_for_unrecognized_exchange_is_unchanged() -> None:
    assert cash_exchange_for("NSE") == "NSE"
    assert cash_exchange_for("MCX") == "MCX"
