"""Tests for MarketWorkspaceService.list_expiries() and
initial_option_chain()'s expiry_date override -- powers the Market tab's
expiry dropdown (and, via the same service call, the Add Leg dialog's)."""

import datetime as _dt
import types
from datetime import date
from decimal import Decimal

import pytest

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.services.market_workspace_service import MarketWorkspaceService
from app.events.event_bus import EventBus
from app.market.bootstrap import MarketMasterProvider
from app.market_data.models.option import OptionChain, OptionStrike


@pytest.fixture
def market_master(tmp_path):
    provider = MarketMasterProvider(tmp_path, EventBus())
    yield provider
    provider.shutdown()


class _FakeMarketDataService:
    """Minimal MarketDataService double: fixed ATM-window chain, no broker/network I/O."""

    def __init__(self) -> None:
        self.get_option_chain_calls: list[tuple] = []

    def get_option_chain(self, underlying: str, exchange: str, expiry_date: str) -> OptionChain:
        self.get_option_chain_calls.append((underlying, exchange, expiry_date))
        strikes = [
            OptionStrike(
                strike_price=Decimal("24500") + Decimal(50 * offset),
                expiry_date=expiry_date,
            )
            for offset in range(-10, 11)
        ]
        return OptionChain(
            underlying=underlying,
            exchange=exchange,
            expiry_date=expiry_date,
            spot_price=Decimal("24523"),
            strikes=strikes,
        )

    def latest_tick(self, symbol: str, exchange: str):
        return None

    def subscribe(self, underlying, exchange, *, product_type, expiry_date="", strike_price="", option_right=""):
        pass


def _make_service(market_master: MarketMasterProvider, market_data: _FakeMarketDataService) -> MarketWorkspaceService:
    engines = types.SimpleNamespace(market_master=market_master)
    return MarketWorkspaceService(engines, None, WorkspaceCache(), market_data=market_data)


class TestListExpiries:
    def test_returns_multiple_upcoming_expiries(self, market_master: MarketMasterProvider) -> None:
        service = _make_service(market_master, _FakeMarketDataService())

        result = service.list_expiries("session-1", "NIFTY", exchange="NFO")

        assert result.success is True
        assert len(result.data) >= 4
        for item in result.data:
            assert set(item.keys()) == {"label", "expiry_date"}

    def test_expiry_dates_are_sorted_and_dd_mon_yyyy_formatted(
        self, market_master: MarketMasterProvider
    ) -> None:
        service = _make_service(market_master, _FakeMarketDataService())

        result = service.list_expiries("session-2", "NIFTY", exchange="NFO")

        dates = [item["expiry_date"] for item in result.data]
        assert dates  # non-empty
        as_dates = [_dt.datetime.strptime(d, "%d-%b-%Y").date() for d in dates]
        assert as_dates == sorted(as_dates)

    def test_unknown_underlying_fails_gracefully(self, market_master: MarketMasterProvider) -> None:
        service = _make_service(market_master, _FakeMarketDataService())

        result = service.list_expiries("session-3", "NOT_A_REAL_SYMBOL", exchange="NFO")

        assert result.success is False


class TestInitialOptionChainExpiryOverride:
    def test_explicit_expiry_date_is_used_verbatim(self, market_master: MarketMasterProvider) -> None:
        market_data = _FakeMarketDataService()
        service = _make_service(market_master, market_data)
        expiries = service.list_expiries("session-4", "NIFTY", exchange="NFO").data
        chosen = expiries[-1]["expiry_date"]  # a later expiry than the auto-resolved nearest one

        result = service.initial_option_chain("session-4", "NIFTY", exchange="NFO", expiry_date=chosen)

        assert result.success is True
        assert result.data["expiry_date"] == chosen
        assert market_data.get_option_chain_calls[0][2] == chosen

    def test_blank_expiry_date_falls_back_to_nearest(self, market_master: MarketMasterProvider) -> None:
        market_data = _FakeMarketDataService()
        service = _make_service(market_master, market_data)

        auto = service.initial_option_chain("session-5", "NIFTY", exchange="NFO")
        explicit_nearest = market_master.expiry_service.nearest_expiry(
            "NIFTY", "NSEFO", on_date=date.today()
        ).expiry_date.strftime("%d-%b-%Y")

        assert auto.data["expiry_date"] == explicit_nearest

    def test_malformed_expiry_date_fails_gracefully(self, market_master: MarketMasterProvider) -> None:
        service = _make_service(market_master, _FakeMarketDataService())

        result = service.initial_option_chain(
            "session-6", "NIFTY", exchange="NFO", expiry_date="not-a-date"
        )

        assert result.success is False
