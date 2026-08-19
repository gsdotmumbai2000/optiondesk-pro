"""Tests for TradingWorkspaceService.leg_chain_strikes(): prefers the
tick-driven live chain (freshest, updates every tick) and falls back to
Market workspace's REST-loaded snapshot (WorkspaceCache
"{session_id}:chain:{underlying}") only when no ticks have landed yet --
using the REST snapshot alone would silently show stale prices for as long
as the dialog stays open while the market moves; using the live cache
alone reproduced the original bug (it can sit empty for a while right
after subscribing even though Market workspace already shows the chain).
"""

from decimal import Decimal
from types import SimpleNamespace

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.services.trading_workspace_service import TradingWorkspaceService
from app.application.session.session_manager import SessionManager
from app.live.models.enums import ChainSide
from app.live.models.option_chain import LiveOptionChain, LiveOptionLeg, LiveOptionStrike


class _FakeLiveAnalyticsPort:
    """Test double for LiveAnalyticsPort: only get_chain() is exercised by
    leg_chain_strikes() (a read-only cache lookup, not a refresh)."""

    def __init__(self, chain: LiveOptionChain | None) -> None:
        self.chain = chain
        self.received: tuple[str, str, str] | None = None

    def get_chain(self, underlying: str, exchange: str, expiry_date: str):
        self.received = (underlying, exchange, expiry_date)
        return self.chain

    def get_analytics(self, underlying, exchange, expiry_date):
        raise AssertionError("not exercised by leg_chain_strikes()")

    def request_refresh(self, underlying, exchange, expiry_date):
        raise AssertionError("not exercised by leg_chain_strikes()")

    def refresh_mode(self):
        raise AssertionError("not exercised by leg_chain_strikes()")

    def refresh_and_get_analytics(self, underlying, exchange, expiry_date):
        raise AssertionError("not exercised by leg_chain_strikes()")


def _live_chain(ltp: str = "999") -> LiveOptionChain:
    call = LiveOptionLeg(
        symbol="NIFTY24500CE", exchange="NFO", underlying="NIFTY", strike_price=Decimal("24500"),
        expiry_date="25-Aug-2026", side=ChainSide.CALL, ltp=Decimal(ltp), open_interest=500,
    )
    return LiveOptionChain(
        underlying="NIFTY", exchange="NFO", expiry_date="25-Aug-2026",
        strikes={"24500": LiveOptionStrike(strike_price=Decimal("24500"), call=call)},
    )


def _payload(expiry_date: str = "25-Aug-2026", strikes: list | None = None) -> dict:
    return {
        "underlying": "NIFTY",
        "exchange": "NFO",
        "expiry_date": expiry_date,
        "strikes": strikes if strikes is not None else [{"strike_price": "24500", "call_ltp": "135.5"}],
    }


def _service(
    session_id: str, payload: dict | None, live_chain: LiveOptionChain | None = None,
) -> TradingWorkspaceService:
    cache = WorkspaceCache()
    if payload is not None:
        cache.put_data(f"{session_id}:chain:NIFTY", payload)
    return TradingWorkspaceService(
        engines=SimpleNamespace(), sessions=SessionManager(), cache=cache,
        live_analytics=_FakeLiveAnalyticsPort(live_chain),
    )


class TestPrefersTheLiveChainWhenTicksHaveArrived:
    def test_live_chain_wins_over_a_stale_rest_snapshot(self) -> None:
        service = _service("s1", _payload(strikes=[{"strike_price": "24500", "call_ltp": "100"}]), _live_chain("135.5"))

        result = service.leg_chain_strikes("s1", "NIFTY", "NFO", "25-Aug-2026")

        assert result.success is True
        assert result.data[0]["call_ltp"] == "135.5"  # live value, not the stale "100" snapshot

    def test_live_chain_works_even_with_no_rest_snapshot_at_all(self) -> None:
        service = _service("s1", None, _live_chain("135.5"))

        result = service.leg_chain_strikes("s1", "NIFTY", "NFO", "25-Aug-2026")

        assert result.success is True
        assert result.data[0]["strike_price"] == "24500"


class TestFallsBackToTheRestSnapshotWhenNoTicksYet:
    def test_returns_the_cached_strikes(self) -> None:
        service = _service("s1", _payload(), live_chain=None)

        result = service.leg_chain_strikes("s1", "NIFTY", "NFO", "25-Aug-2026")

        assert result.success is True
        assert result.data == [{"strike_price": "24500", "call_ltp": "135.5"}]

    def test_empty_live_chain_also_falls_back(self) -> None:
        empty_live_chain = LiveOptionChain(underlying="NIFTY", exchange="NFO", expiry_date="25-Aug-2026")
        service = _service("s1", _payload(), empty_live_chain)

        result = service.leg_chain_strikes("s1", "NIFTY", "NFO", "25-Aug-2026")

        assert result.success is True
        assert result.data == [{"strike_price": "24500", "call_ltp": "135.5"}]


class TestBothSourcesUnavailable:
    def test_underlying_never_loaded_in_market_workspace_fails_softly(self) -> None:
        service = _service("s1", None, live_chain=None)

        result = service.leg_chain_strikes("s1", "NIFTY", "NFO", "25-Aug-2026")

        assert result.success is False
        assert "subscribe" in result.message.lower()

    def test_empty_strikes_list_fails_softly(self) -> None:
        service = _service("s1", _payload(strikes=[]), live_chain=None)

        result = service.leg_chain_strikes("s1", "NIFTY", "NFO", "25-Aug-2026")

        assert result.success is False

    def test_wrong_session_id_does_not_see_another_sessions_chain(self) -> None:
        service = _service("s1", _payload(), live_chain=None)

        result = service.leg_chain_strikes("s2", "NIFTY", "NFO", "25-Aug-2026")

        assert result.success is False

    def test_expiry_mismatch_fails_with_a_helpful_message(self) -> None:
        service = _service("s1", _payload(expiry_date="18-Aug-2026"), live_chain=None)

        result = service.leg_chain_strikes("s1", "NIFTY", "NFO", "25-Aug-2026")

        assert result.success is False
        assert "18-Aug-2026" in result.message
        assert "25-Aug-2026" in result.message
