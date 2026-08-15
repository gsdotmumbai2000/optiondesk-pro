"""Tests for Breeze option chain normalization: field extraction and CALL/PUT merge."""

from decimal import Decimal

from app.brokers.breeze.normalizers.option_chain_normalizer import normalize_option_chain


def _call_row(strike: str = "24500", **extra) -> dict:
    row = {
        "strike_price": strike,
        "right": "call",
        "stock_code": "NIFTY24500CE",
        "ltp": "120.5",
        "best_bid_price": "119.5",
        "best_offer_price": "121.5",
        "open_interest": "45000",
        "total_quantity_traded": "98000",
        "spot_price": "24510",
    }
    row.update(extra)
    return row


def _put_row(strike: str = "24500", **extra) -> dict:
    row = {
        "strike_price": strike,
        "right": "put",
        "stock_code": "NIFTY24500PE",
        "ltp": "80.25",
        "best_bid_price": "79.25",
        "best_offer_price": "81.25",
        "open_interest": "38000",
        "total_quantity_traded": "76000",
        "spot_price": "24510",
    }
    row.update(extra)
    return row


def test_call_and_put_rows_merge_into_one_strike_row() -> None:
    chain = normalize_option_chain("NIFTY", "NFO", "13-Feb-2026", [_call_row(), _put_row()])

    assert len(chain.rows) == 1
    leg = chain.rows[0]
    assert leg.strike_price == Decimal("24500")
    assert leg.call_symbol == "NIFTY24500CE"
    assert leg.put_symbol == "NIFTY24500PE"


def test_bid_ask_oi_volume_normalize_correctly() -> None:
    chain = normalize_option_chain("NIFTY", "NFO", "13-Feb-2026", [_call_row(), _put_row()])
    leg = chain.rows[0]

    assert leg.call_bid == Decimal("119.5")
    assert leg.call_ask == Decimal("121.5")
    assert leg.call_oi == 45000
    assert leg.call_volume == 98000
    assert leg.put_bid == Decimal("79.25")
    assert leg.put_ask == Decimal("81.25")
    assert leg.put_oi == 38000
    assert leg.put_volume == 76000


def test_no_fake_iv_is_generated_when_broker_omits_it() -> None:
    chain = normalize_option_chain("NIFTY", "NFO", "13-Feb-2026", [_call_row(), _put_row()])
    leg = chain.rows[0]

    assert leg.call_iv is None
    assert leg.put_iv is None


def test_iv_passes_through_when_broker_provides_it() -> None:
    chain = normalize_option_chain(
        "NIFTY", "NFO", "13-Feb-2026", [_call_row(implied_volatility="14.2")]
    )

    assert chain.rows[0].call_iv == Decimal("14.2")


def test_multiple_strikes_each_produce_one_merged_row() -> None:
    chain = normalize_option_chain(
        "NIFTY",
        "NFO",
        "13-Feb-2026",
        [_call_row("24500"), _put_row("24500"), _call_row("24600"), _put_row("24600")],
    )

    assert len(chain.rows) == 2
    assert [leg.strike_price for leg in chain.rows] == [Decimal("24500"), Decimal("24600")]


def test_spot_price_taken_from_broker_payload_when_not_supplied() -> None:
    chain = normalize_option_chain("NIFTY", "NFO", "13-Feb-2026", [_call_row()])

    assert chain.spot_price == Decimal("24510")


def test_atm_strike_flag_set_only_when_atm_strike_supplied() -> None:
    chain = normalize_option_chain(
        "NIFTY",
        "NFO",
        "13-Feb-2026",
        [_call_row("24500"), _call_row("24600")],
        atm_strike=Decimal("24600"),
    )

    by_strike = {leg.strike_price: leg for leg in chain.rows}
    assert by_strike[Decimal("24500")].is_atm is False
    assert by_strike[Decimal("24600")].is_atm is True
