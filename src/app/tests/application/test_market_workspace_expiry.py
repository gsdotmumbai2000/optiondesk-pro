"""Regression tests for MarketWorkspaceService.initial_option_chain() expiry resolution.

Live-runtime bug: initial_option_chain() called
`expiry_service.weekly_expiry(...)`, but ExpiryService (app.market.expiries.
service.ExpiryService) has no such method — only InstrumentService does, as
a thin wrapper delegating to ExpiryService's own
nearest_expiry(..., expiry_type=ExpiryType.WEEKLY). Every live Option Chain
load therefore failed immediately with:

    AttributeError: 'ExpiryService' object has no attribute 'weekly_expiry'

before ever reaching MarketDataService/BreezeOptionChain. These tests use
the real ExpiryService/InstrumentService (via MarketMasterProvider), only
faking the MarketDataService/broker boundary, so they exercise the actual
production API surface rather than a mocked one.
"""

import types
from datetime import date
from decimal import Decimal

import pytest

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.services.market_workspace_service import MarketWorkspaceService
from app.brokers.shared.enums import ProductType
from app.events.event_bus import EventBus
from app.market.bootstrap import MarketMasterProvider
from app.market.enums import ExpiryType
from app.market.expiries.service import ExpiryService
from app.market_data.models.option import OptionChain, OptionStrike


@pytest.fixture
def market_master(tmp_path):
    """Real Market Master provider (same construction as test_services.py)."""
    provider = MarketMasterProvider(tmp_path, EventBus())
    yield provider
    provider.shutdown()


class _FakeMarketDataService:
    """Minimal MarketDataService double: fixed ATM-window chain, no broker/network I/O."""

    def __init__(self) -> None:
        self.get_option_chain_calls: list[tuple] = []
        self.subscribe_calls: list[tuple] = []

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

    def subscribe(
        self,
        underlying: str,
        exchange: str,
        *,
        product_type,
        expiry_date: str = "",
        strike_price: str = "",
        option_right: str = "",
    ) -> None:
        self.subscribe_calls.append(
            (product_type, underlying, exchange, expiry_date, strike_price, option_right)
        )


def _make_service(
    market_master: MarketMasterProvider, market_data: _FakeMarketDataService
) -> MarketWorkspaceService:
    engines = types.SimpleNamespace(market_master=market_master)
    return MarketWorkspaceService(engines, None, WorkspaceCache(), market_data=market_data)


class TestExpiryServiceRealAPI:
    """ExpiryService's real public API, as it actually exists in source."""

    def test_expiry_service_has_no_weekly_expiry_method(
        self, market_master: MarketMasterProvider
    ) -> None:
        """Documents the exact precondition of the bug: no weekly_expiry() on ExpiryService."""
        assert not hasattr(market_master.expiry_service, "weekly_expiry")

    def test_expiry_service_nearest_expiry_resolves_weekly_by_default(
        self, market_master: MarketMasterProvider
    ) -> None:
        """nearest_expiry() defaults to expiry_type=WEEKLY — the real replacement API."""
        record = market_master.expiry_service.nearest_expiry(
            "NIFTY", "NSEFO", on_date=date(2026, 1, 5)
        )
        assert record is not None
        assert record.expiry_type == ExpiryType.WEEKLY


class TestInitialOptionChainResolvesExpiry:
    """initial_option_chain() must resolve expiry via the real ExpiryService API."""

    def test_initial_option_chain_does_not_raise_attribute_error(
        self, market_master: MarketMasterProvider
    ) -> None:
        """End-to-end proof: calling the real (non-mocked) ExpiryService no
        longer raises AttributeError, and the ATM window is produced using
        a dynamically resolved expiry (never hardcoded)."""
        market_data = _FakeMarketDataService()
        service = _make_service(market_master, market_data)

        result = service.initial_option_chain("session-1", "NIFTY", exchange="NFO")

        assert result.success is True
        assert len(market_data.get_option_chain_calls) == 1
        underlying, exchange, expiry_date = market_data.get_option_chain_calls[0]
        assert underlying == "NIFTY"
        assert exchange == "NFO"
        assert expiry_date  # dynamically resolved, non-empty
        assert result.data["strikes"]
        assert result.data["atm_strike"] == "24500"

    def test_initial_option_chain_calls_expiry_service_nearest_expiry(
        self, market_master: MarketMasterProvider, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Explicit regression guard for item 9: fails if the call site is
        ever changed to reference the nonexistent weekly_expiry() again,
        since nearest_expiry() would then never be invoked (and the real
        call would instead raise AttributeError before reaching this spy).

        Task 10: initial_option_chain() now calls nearest_expiry() twice --
        once for the weekly option expiry (default expiry_type), once for
        the monthly futures expiry (expiry_type=MONTHLY) -- so this guards
        both calls happen with the expected, distinct expiry_type."""
        calls: list[tuple] = []
        original = ExpiryService.nearest_expiry

        def spy(self, *args, **kwargs):
            calls.append((args, kwargs))
            return original(self, *args, **kwargs)

        monkeypatch.setattr(ExpiryService, "nearest_expiry", spy)

        market_data = _FakeMarketDataService()
        service = _make_service(market_master, market_data)

        result = service.initial_option_chain("session-2", "NIFTY", exchange="NFO")

        assert result.success is True
        assert len(calls) == 2
        weekly_kwargs = calls[0][1]
        monthly_kwargs = calls[1][1]
        assert "expiry_type" not in weekly_kwargs  # defaults to WEEKLY
        assert monthly_kwargs["expiry_type"] == ExpiryType.MONTHLY


class TestInitialOptionChainSubscribesFuture:
    """Task 9: initial_option_chain() must subscribe the underlying's future
    at the same dynamically-resolved expiry, so get_future() has a live tick
    to find. Missing this caused every live calculation for NFO:NIFTY:<expiry>
    to fail with 'Future quote unavailable: NIFTY' (534/534 in live testing)."""

    def test_required_future_causes_exactly_one_subscription(
        self, market_master: MarketMasterProvider
    ) -> None:
        market_data = _FakeMarketDataService()
        service = _make_service(market_master, market_data)

        result = service.initial_option_chain("session-3", "NIFTY", exchange="NFO")
        assert result.success is True

        future_calls = [
            call for call in market_data.subscribe_calls if call[0] == ProductType.FUTURES
        ]
        assert len(future_calls) == 1
        _product_type, underlying, exchange, expiry_date, strike_price, option_right = (
            future_calls[0]
        )
        assert underlying == "NIFTY"
        assert exchange == "NFO"
        assert expiry_date  # dynamically resolved, non-empty, never hardcoded
        assert strike_price == ""
        assert option_right == ""

    def test_future_subscription_uses_its_own_monthly_expiry_not_the_weekly_option_expiry(
        self, market_master: MarketMasterProvider
    ) -> None:
        """Task 10: NIFTY-family futures expire monthly while options expire
        weekly, so the future subscription must resolve its own monthly
        expiry independently -- reusing the option window's weekly expiry
        made every live futures subscription request a contract Breeze has
        no token for ('stock_code was not found in Breeze's own scrip
        dictionary'). Each value is verified against the real ExpiryService
        resolution for its own expiry_type, not asserted equal to the other."""
        market_data = _FakeMarketDataService()
        service = _make_service(market_master, market_data)

        service.initial_option_chain("session-4", "NIFTY", exchange="NFO")

        option_expiries = {
            call[3] for call in market_data.subscribe_calls if call[0] == ProductType.OPTIONS
        }
        future_expiries = {
            call[3] for call in market_data.subscribe_calls if call[0] == ProductType.FUTURES
        }
        assert len(option_expiries) == 1
        assert len(future_expiries) == 1

        expected_option_expiry = market_master.expiry_service.nearest_expiry(
            "NIFTY", "NSEFO", on_date=date.today()
        ).expiry_date.strftime("%d-%b-%Y")
        expected_future_expiry = market_master.expiry_service.nearest_expiry(
            "NIFTY", "NSEFO", on_date=date.today(), expiry_type=ExpiryType.MONTHLY
        ).expiry_date.strftime("%d-%b-%Y")

        assert option_expiries == {expected_option_expiry}
        assert future_expiries == {expected_future_expiry}
        # True for real "today" data (18-Aug-2026 weekly vs 25-Aug-2026
        # monthly) -- not a hard invariant of the expiry engine (a weekly
        # Tuesday can coincide with the month's last Tuesday), but this is
        # the exact scenario Task 10 requires proving.
        assert future_expiries != option_expiries

    def test_next_expiry_produces_a_subscription_for_the_new_contract(
        self, market_master: MarketMasterProvider, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Simulates an expiry rollover: nearest_expiry() resolving to a later
        date must cause the future subscription's expiry_date to move with
        it, proving the value is read live from the expiry resolver rather
        than cached or hardcoded from the first call."""
        market_data = _FakeMarketDataService()
        service = _make_service(market_master, market_data)

        service.initial_option_chain("session-5", "NIFTY", exchange="NFO")
        first_future = next(
            call for call in market_data.subscribe_calls if call[0] == ProductType.FUTURES
        )
        first_expiry = first_future[3]

        original = ExpiryService.nearest_expiry

        def next_week(self, *args, **kwargs):
            from datetime import timedelta

            record = original(self, *args, **kwargs)
            return record.model_copy(update={"expiry_date": record.expiry_date + timedelta(days=7)})

        monkeypatch.setattr(ExpiryService, "nearest_expiry", next_week)

        service.initial_option_chain("session-6", "NIFTY", exchange="NFO")
        rolled_future = [
            call for call in market_data.subscribe_calls if call[0] == ProductType.FUTURES
        ][-1]
        rolled_expiry = rolled_future[3]

        assert rolled_expiry != first_expiry

    def test_repeated_chain_loads_do_not_multiply_subscribe_calls(
        self, market_master: MarketMasterProvider
    ) -> None:
        """initial_option_chain() itself issues exactly one future subscribe
        call per invocation (broker-level dedup is SubscriptionService's job,
        covered in test_subscription_service.py); this guards the call site
        from regressing into a loop or duplicate call per invocation."""
        market_data = _FakeMarketDataService()
        service = _make_service(market_master, market_data)

        for session in ("session-7", "session-8", "session-9"):
            service.initial_option_chain(session, "NIFTY", exchange="NFO")

        future_calls = [
            call for call in market_data.subscribe_calls if call[0] == ProductType.FUTURES
        ]
        assert len(future_calls) == 3  # one per invocation, not accumulating extras

    def test_future_subscription_failure_does_not_abort_option_chain_loading(
        self, market_master: MarketMasterProvider
    ) -> None:
        """Live regression: a broker-level failure subscribing the future
        (e.g. no futures contract exists at this expiry -- confirmed live,
        Breeze SDK raised RuntimeError: 'stock_code was not found in
        Breeze's own scrip dictionary') must not propagate out of
        initial_option_chain() and abort the REST chain fetch / option
        window subscription that follows it. Reproduces the exact live
        failure: subscribe() raising for FUTURES took get_option_chain_calls
        and the option subscribe_calls to zero before this fix."""

        class _FailingFutureMarketDataService(_FakeMarketDataService):
            def subscribe(self, underlying, exchange, *, product_type, **kwargs):
                if product_type == ProductType.FUTURES:
                    raise RuntimeError(
                        "Exception while subscribing to feeds Breeze returned an "
                        "invalid token for stock_code='NIFTY' exchange_code='NFO'"
                    )
                super().subscribe(underlying, exchange, product_type=product_type, **kwargs)

        market_data = _FailingFutureMarketDataService()
        service = _make_service(market_master, market_data)

        result = service.initial_option_chain("session-10", "NIFTY", exchange="NFO")

        assert result.success is True
        assert len(market_data.get_option_chain_calls) == 1
        option_calls = [
            call for call in market_data.subscribe_calls if call[0] == ProductType.OPTIONS
        ]
        assert len(option_calls) == 21 * 2
