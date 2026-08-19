"""Tests for TradingWorkspaceService.list_underlyings() and
leg_builder_context(): the pure Instrument/Expiry Master lookups behind the
Strategy Builder's "Add Leg" dialog. Real MarketMasterProvider against the
real seed data (RESOURCES_DIR/market), same construction pattern as
test_option_chain_pipeline_end_to_end.py -- no broker, no live ticks.
"""

from types import SimpleNamespace

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.services.trading_workspace_service import TradingWorkspaceService
from app.application.session.session_manager import SessionManager
from app.events.event_bus import EventBus
from app.market.bootstrap import MarketMasterProvider


def _service(tmp_path) -> TradingWorkspaceService:
    market_master = MarketMasterProvider(tmp_path, EventBus())
    engines = SimpleNamespace(market_master=market_master)
    return TradingWorkspaceService(
        engines=engines, sessions=SessionManager(), cache=WorkspaceCache(),
    )


class TestListUnderlyings:
    def test_returns_known_index_underlyings(self, tmp_path) -> None:
        service = _service(tmp_path)

        result = service.list_underlyings()

        assert result.success is True
        assert "NIFTY" in result.data

    def test_underlyings_are_deduplicated_and_sorted(self, tmp_path) -> None:
        service = _service(tmp_path)

        result = service.list_underlyings()

        assert result.data == sorted(set(result.data))


class TestLegBuilderContext:
    def test_known_underlying_returns_expiries_and_lot_size(self, tmp_path) -> None:
        service = _service(tmp_path)

        result = service.leg_builder_context("NIFTY")

        assert result.success is True
        assert result.data["lot_size"] > 0
        assert len(result.data["expiries"]) >= 1
        label, expiry_date = result.data["expiries"][0]
        assert "Weekly" in label or "Monthly" in label
        assert expiry_date is not None

    def test_unknown_underlying_fails_softly(self, tmp_path) -> None:
        service = _service(tmp_path)

        result = service.leg_builder_context("NOT_A_REAL_UNDERLYING")

        assert result.success is False
        assert result.data is None
