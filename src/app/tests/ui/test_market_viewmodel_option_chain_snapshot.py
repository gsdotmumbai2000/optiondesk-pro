"""Tests for MarketViewModel._snapshot_from_rest_chain()/_snapshot_from_live_
chain(): build a real OptionChainSnapshot (the type VolatilityChartWidget.
set_chain() needs) from initial_option_chain()'s REST payload and from a
LiveOptionChainUpdatedEvent payload, respectively -- previously only
pre-formatted display rows were emitted, never the raw snapshot.
"""

from decimal import Decimal

from app.calculation.models.snapshots import OptionChainSnapshot
from app.ui.viewmodels.market_viewmodel import MarketViewModel


def _rest_strike(price: str = "24500", **overrides) -> dict:
    row = {
        "strike_price": price,
        "expiry_date": "18-Aug-2026",
        "call_symbol": "NIFTY24500CE",
        "put_symbol": "NIFTY24500PE",
        "call_ltp": "120.5",
        "put_ltp": "95.25",
        "call_oi": 45000,
        "put_oi": 38000,
        "call_iv": "14.2",
        "put_iv": "15.8",
        "is_atm": False,
    }
    row.update(overrides)
    return row


def _rest_payload(**overrides) -> dict:
    payload = {
        "underlying": "NIFTY",
        "exchange": "NFO",
        "expiry_date": "18-Aug-2026",
        "spot_price": "24450",
        "atm_strike": "24450",
        "strikes": [_rest_strike()],
    }
    payload.update(overrides)
    return payload


class TestSnapshotFromRestChain:
    def test_builds_real_option_chain_snapshot(self) -> None:
        snapshot = MarketViewModel._snapshot_from_rest_chain(_rest_payload())

        assert isinstance(snapshot, OptionChainSnapshot)
        assert snapshot.underlying == "NIFTY"
        assert snapshot.exchange == "NFO"
        assert snapshot.expiry_date == "18-Aug-2026"
        assert snapshot.spot_price == Decimal("24450")
        assert snapshot.atm_strike == Decimal("24450")

    def test_strike_iv_and_price_fields_parsed_as_decimal(self) -> None:
        snapshot = MarketViewModel._snapshot_from_rest_chain(_rest_payload())

        strike = snapshot.strikes[0]
        assert strike.strike_price == Decimal("24500")
        assert strike.call_iv == Decimal("14.2")
        assert strike.put_iv == Decimal("15.8")
        assert strike.call_ltp == Decimal("120.5")
        assert strike.call_oi == 45000

    def test_multiple_strikes_all_preserved_in_order(self) -> None:
        payload = _rest_payload(strikes=[_rest_strike("24400"), _rest_strike("24500"), _rest_strike("24600")])

        snapshot = MarketViewModel._snapshot_from_rest_chain(payload)

        assert [s.strike_price for s in snapshot.strikes] == [
            Decimal("24400"), Decimal("24500"), Decimal("24600"),
        ]

    def test_missing_iv_becomes_none_not_fabricated(self) -> None:
        payload = _rest_payload(strikes=[_rest_strike(call_iv=None, put_iv=None)])

        snapshot = MarketViewModel._snapshot_from_rest_chain(payload)

        assert snapshot.strikes[0].call_iv is None
        assert snapshot.strikes[0].put_iv is None

    def test_no_underlying_returns_none(self) -> None:
        payload = _rest_payload(underlying=None)

        assert MarketViewModel._snapshot_from_rest_chain(payload) is None

    def test_strike_without_strike_price_is_skipped(self) -> None:
        payload = _rest_payload(strikes=[_rest_strike(strike_price=None), _rest_strike("24500")])

        snapshot = MarketViewModel._snapshot_from_rest_chain(payload)

        assert len(snapshot.strikes) == 1
        assert snapshot.strikes[0].strike_price == Decimal("24500")

    def test_is_atm_flag_preserved(self) -> None:
        payload = _rest_payload(strikes=[_rest_strike(is_atm=True)])

        snapshot = MarketViewModel._snapshot_from_rest_chain(payload)

        assert snapshot.strikes[0].is_atm is True


def _live_leg(**overrides) -> dict:
    leg = {
        "symbol": "NIFTY24500CE", "exchange": "NFO", "underlying": "NIFTY",
        "strike_price": "24500", "expiry_date": "18-Aug-2026", "side": "CALL",
        "ltp": "120.5", "implied_volatility": "14.2",
    }
    leg.update(overrides)
    return leg


def _live_chain_payload(**overrides) -> dict:
    payload = {
        "underlying": "NIFTY",
        "exchange": "NFO",
        "expiry_date": "18-Aug-2026",
        "spot_price": "24450",
        "atm_strike": "24450",
        "strikes": {
            "24500": {
                "strike_price": "24500",
                "call": _live_leg(),
                "put": _live_leg(side="PUT", symbol="NIFTY24500PE", implied_volatility="15.8"),
                "is_atm": True,
            },
        },
    }
    payload.update(overrides)
    return payload


class TestSnapshotFromLiveChain:
    def test_builds_real_option_chain_snapshot_via_chain_builder(self) -> None:
        snapshot = MarketViewModel._snapshot_from_live_chain(_live_chain_payload())

        assert isinstance(snapshot, OptionChainSnapshot)
        assert snapshot.underlying == "NIFTY"
        assert snapshot.exchange == "NFO"
        assert len(snapshot.strikes) == 1
        strike = snapshot.strikes[0]
        assert strike.strike_price == Decimal("24500")
        assert strike.call_iv == Decimal("14.2")
        assert strike.put_iv == Decimal("15.8")
        assert strike.is_atm is True

    def test_malformed_payload_returns_none_not_raises(self) -> None:
        assert MarketViewModel._snapshot_from_live_chain({"strikes": "not-a-dict"}) is None

    def test_missing_required_fields_returns_none(self) -> None:
        assert MarketViewModel._snapshot_from_live_chain({}) is None
