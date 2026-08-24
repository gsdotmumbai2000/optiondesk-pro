"""Tests for LiveContextBuilder.build_option_chain(): prefers the
tick-driven live chain and falls back to the REST-loaded chain snapshot
already resolved onto the CalculationContext when no tick has streamed in
yet -- e.g. market closed, or Evaluate/Optimize clicked right after
subscribing. Previously this required a live tick unconditionally, so
Evaluate failed with "Live chain unavailable" even when the same chain
data was already sitting on the context from a REST call.
"""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.live.calculations.context_builder import LiveContextBuilder
from app.live.models.chain_key import ChainKey
from app.live.models.enums import ChainSide
from app.live.models.option_chain import LiveOptionChain, LiveOptionLeg, LiveOptionStrike

_KEY = ChainKey("NIFTY", "NFO", "25-Aug-2026")


class _FakeChainManager:
    def __init__(self, chain: LiveOptionChain | None) -> None:
        self.chain = chain
        self.received: ChainKey | None = None

    def get_chain(self, key: ChainKey):
        self.received = key
        return self.chain


def _live_chain() -> LiveOptionChain:
    call = LiveOptionLeg(
        symbol="NIFTY24500CE", exchange="NFO", underlying="NIFTY", strike_price=Decimal("24500"),
        expiry_date="25-Aug-2026", side=ChainSide.CALL, ltp=Decimal("135.5"),
    )
    return LiveOptionChain(
        underlying="NIFTY", exchange="NFO", expiry_date="25-Aug-2026",
        strikes={"24500": LiveOptionStrike(strike_price=Decimal("24500"), call=call)},
    )


def _builder(chain_manager: _FakeChainManager) -> LiveContextBuilder:
    return LiveContextBuilder(context_service=None, chain_manager=chain_manager)


class TestPrefersTheLiveChain:
    def test_returns_the_live_chain_when_ticks_have_arrived(self) -> None:
        builder = _builder(_FakeChainManager(_live_chain()))
        context = SimpleNamespace(option_chain_snapshot="rest-snapshot-should-not-be-used")

        result = builder.build_option_chain(_KEY, context)

        assert result.underlying == "NIFTY"  # converted from the live chain, not the REST fallback


class TestFallsBackToTheRestSnapshot:
    def test_uses_context_option_chain_snapshot_when_no_ticks_yet(self) -> None:
        builder = _builder(_FakeChainManager(None))
        rest_snapshot = SimpleNamespace(name="rest-snapshot")
        context = SimpleNamespace(option_chain_snapshot=rest_snapshot)

        result = builder.build_option_chain(_KEY, context)

        assert result is rest_snapshot

    def test_looks_up_the_correct_chain_key_before_falling_back(self) -> None:
        chain_manager = _FakeChainManager(None)
        builder = _builder(chain_manager)
        context = SimpleNamespace(option_chain_snapshot=SimpleNamespace())

        builder.build_option_chain(_KEY, context)

        assert chain_manager.received == _KEY


class TestBothSourcesUnavailable:
    def test_raises_when_neither_live_nor_rest_data_exists(self) -> None:
        builder = _builder(_FakeChainManager(None))
        context = SimpleNamespace(option_chain_snapshot=None)

        with pytest.raises(ValueError, match="Live chain unavailable"):
            builder.build_option_chain(_KEY, context)
