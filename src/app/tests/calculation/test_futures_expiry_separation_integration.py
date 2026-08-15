"""Task 10 Phase D, Test 3 + Test 8: integration proof that the futures
subscription (application layer, MarketWorkspaceService) and the futures
lookup (calculation layer, CalculationContextFactory.get_future()) resolve
to the *identical* monthly expiry -- both independently call the same real
ExpiryService, so a divergence here would silently break get_future() even
after a correctly-issued subscription (a cache-key mismatch, same failure
class as Task 1's quote_key() bug, just at the expiry-value layer instead
of the signature layer).

Uses the real ExpiryService/MarketMasterProvider on both sides (never a
fake expiry calendar) so this proves the two production call paths agree,
not just that each independently calls *some* mock correctly.
"""

import types
from datetime import date, datetime
from decimal import Decimal

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.services.market_workspace_service import MarketWorkspaceService
from app.brokers.shared.enums import ProductType
from app.calculation.factory.context_factory import CalculationContextFactory
from app.calculation.providers.adapters import ExpiryCalendarPortAdapter
from app.calculation.providers.dividend_provider import DividendProvider
from app.calculation.providers.expiry_provider import ExpiryProvider
from app.calculation.providers.interest_rate_provider import InterestRateProvider
from app.calculation.providers.market_status_provider import MarketStatusProvider
from app.calculation.providers.time_provider import TimeProvider
from app.calculation.providers.volatility_provider import VolatilityProvider
from app.events.event_bus import EventBus
from app.market.bootstrap import MarketMasterProvider
from app.market_data.models.option import OptionChain, OptionStrike


class _FakeWorkspaceMarketData:
    """MarketWorkspaceService's market-data surface: records subscribe() calls."""

    def __init__(self) -> None:
        self.subscribe_calls: list[tuple] = []

    def get_option_chain(self, underlying: str, exchange: str, expiry_date: str) -> OptionChain:
        strikes = [
            OptionStrike(strike_price=Decimal("24500"), expiry_date=expiry_date)
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
        self.subscribe_calls.append((product_type, underlying, exchange, expiry_date))


class _FakeCalcMarketData:
    """CalculationContextFactory's IMarketDataQueryPort: records get_future()'s expiry_date."""

    def __init__(self) -> None:
        self.future_expiry_date: str | None = None

    def get_spot(self, symbol: str, exchange: str):
        return types.SimpleNamespace(ltp=Decimal("24500"), timestamp=None)

    def get_future(self, symbol: str, exchange: str, expiry_date: str):
        self.future_expiry_date = expiry_date
        return types.SimpleNamespace(
            ltp=Decimal("24600"), underlying=symbol, open_interest=None, volume=None, timestamp=None
        )

    def get_option_chain(self, underlying: str, exchange: str, expiry_date: str):
        return types.SimpleNamespace(
            underlying=underlying,
            exchange=exchange,
            expiry_date=expiry_date,
            spot_price=Decimal("24500"),
            atm_strike=Decimal("24500"),
            strikes=(),
        )

    def get_atm_strike(self, underlying: str, exchange: str, expiry_date: str):
        return Decimal("24500")


class _FixedInstruments:
    def get_lot_size(self, underlying: str) -> int:
        return 75

    def get_tick_size(self, underlying: str) -> Decimal:
        return Decimal("0.05")

    def get_strike_interval(self, underlying: str) -> Decimal:
        return Decimal("50")


class _AlwaysOpenMarketStatus:
    def is_market_open(self, exchange: str, moment: datetime) -> bool:
        return True

    def trade_date(self, exchange: str, moment: datetime) -> date:
        return moment.date()


def test_subscription_and_get_future_resolve_the_identical_monthly_expiry(tmp_path) -> None:
    market_master = MarketMasterProvider(tmp_path, EventBus())
    try:
        # -- Subscription side (application layer) --
        workspace_market_data = _FakeWorkspaceMarketData()
        engines = types.SimpleNamespace(market_master=market_master)
        workspace = MarketWorkspaceService(
            engines, None, WorkspaceCache(), market_data=workspace_market_data
        )
        result = workspace.initial_option_chain("session-1", "NIFTY", exchange="NFO")
        assert result.success is True

        future_subscribe_calls = [
            call for call in workspace_market_data.subscribe_calls
            if call[0] == ProductType.FUTURES
        ]
        assert len(future_subscribe_calls) == 1
        subscribed_expiry = future_subscribe_calls[0][3]

        # -- Lookup side (calculation layer) -- bridges the SAME real
        # ExpiryService through ExpiryCalendarPortAdapter, exactly as
        # live/bootstrap.py wires CalculationProvider.from_services(). --
        calc_market_data = _FakeCalcMarketData()
        factory = CalculationContextFactory(
            calc_market_data,
            _FixedInstruments(),
            ExpiryProvider(ExpiryCalendarPortAdapter(market_master.expiry_service)),
            InterestRateProvider(),
            DividendProvider(),
            VolatilityProvider(),
            MarketStatusProvider(_AlwaysOpenMarketStatus(), TimeProvider()),
        )
        weekly_expiry_record = market_master.expiry_service.nearest_expiry(
            "NIFTY", "NSEFO", on_date=date.today()
        )
        factory.build("NIFTY", "NFO", weekly_expiry_record.expiry_date.strftime("%d-%b-%Y"))

        assert calc_market_data.future_expiry_date is not None
        assert calc_market_data.future_expiry_date == subscribed_expiry
    finally:
        market_master.shutdown()
