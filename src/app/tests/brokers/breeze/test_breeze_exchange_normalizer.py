"""Tests for canonical_exchange(): raw Breeze tick exchange label mapping."""

from app.brokers.breeze.normalizers.exchange_normalizer import canonical_exchange


def test_nse_equity_label_maps_to_nse() -> None:
    assert canonical_exchange("NSE Equity") == "NSE"


def test_nse_futures_and_options_label_maps_to_nfo() -> None:
    assert canonical_exchange("NSE Futures & Options") == "NFO"


def test_bse_label_is_already_canonical() -> None:
    assert canonical_exchange("BSE") == "BSE"


def test_unrecognized_label_is_returned_unchanged() -> None:
    assert canonical_exchange("NSE Currency") == "NSE Currency"
    assert canonical_exchange("Commodity") == "Commodity"


def test_already_canonical_codes_are_left_unchanged() -> None:
    assert canonical_exchange("NSE") == "NSE"
    assert canonical_exchange("NFO") == "NFO"
