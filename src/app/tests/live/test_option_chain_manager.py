"""Tests for OptionChainManager aggregating CALL/PUT ticks into one strike row.

Uses the real deterministic canonical option symbol (as produced by
WebSocketService for live option ticks) to confirm the existing live
pipeline (WebSocketService -> TickSnapshot -> OptionChainManager) still
resolves the underlying and strike correctly without any chain_manager
changes.
"""

from datetime import datetime, timezone
from decimal import Decimal

from app.live.cache.option_cache import LiveOptionCache
from app.live.models.chain_key import ChainKey
from app.live.models.enums import ChainSide
from app.live.option_chain.chain_manager import OptionChainManager
from app.market_data.models.tick import TickSnapshot
from app.market_data.symbols import build_option_contract_symbol


def _option_tick(strike: str, right: str, ltp: str) -> TickSnapshot:
    return TickSnapshot(
        symbol=build_option_contract_symbol("NIFTY", "13-Feb-2026", strike, right),
        broker_symbol="4.1!51219",
        exchange="NFO",
        ltp=Decimal(ltp),
        product_type="OPTIONS",
        expiry_date="13-Feb-2026",
        strike_price=strike,
        option_right=right,
        timestamp=datetime.now(timezone.utc),
    )


def test_call_and_put_ticks_create_both_sides_of_same_strike() -> None:
    manager = OptionChainManager(LiveOptionCache())

    manager.apply_tick(_option_tick("24500", "Call", "120.5"))
    manager.apply_tick(_option_tick("24500", "Put", "80.25"))

    chain = manager.get_chain(ChainKey("NIFTY", "NFO", "13-Feb-2026"))
    assert chain is not None
    row = chain.strikes["24500"]
    assert row.call is not None
    assert row.call.side == ChainSide.CALL
    assert row.call.ltp == Decimal("120.5")
    assert row.put is not None
    assert row.put.side == ChainSide.PUT
    assert row.put.ltp == Decimal("80.25")


def test_underlying_resolved_from_canonical_option_symbol() -> None:
    manager = OptionChainManager(LiveOptionCache())

    chain = manager.apply_tick(_option_tick("24500", "Call", "120.5"))

    assert chain is not None
    assert chain.underlying == "NIFTY"
    assert chain.expiry_date == "13-Feb-2026"


def test_put_only_tick_does_not_populate_call_side() -> None:
    manager = OptionChainManager(LiveOptionCache())

    chain = manager.apply_tick(_option_tick("24500", "Put", "80.25"))

    assert chain is not None
    row = chain.strikes["24500"]
    assert row.put is not None
    assert row.call is None
