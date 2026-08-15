"""Regression coverage for spot lookups using the cash exchange, not the
option contract's exchange.

CalculationContextFactory._assemble() used to pass the same exchange to
get_spot(), get_future(), and get_option_chain() - the exchange the caller
built the context with, which for a live NIFTY option chain is "NFO". A spot/
index quote for NIFTY only ever exists on its cash exchange ("NSE"), never on
NFO, so get_spot() was structurally asking for data that could never exist
under that key. get_future()/get_option_chain() still need the NFO exchange
unchanged.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.calculation.factory.context_factory import CalculationContextFactory
from app.calculation.models.snapshots import FutureQuoteSnapshot, SpotQuoteSnapshot
from app.calculation.providers.dividend_provider import DividendProvider
from app.calculation.providers.expiry_provider import ExpiryProvider
from app.calculation.providers.interest_rate_provider import InterestRateProvider
from app.calculation.providers.market_status_provider import MarketStatusProvider
from app.calculation.providers.time_provider import TimeProvider
from app.calculation.providers.volatility_provider import VolatilityProvider


@dataclass
class _RecordingMarketData:
    """Fake IMarketDataQueryPort recording the exchange/expiry each call received."""

    spot_exchange: str | None = None
    future_exchange: str | None = None
    option_chain_exchange: str | None = None
    future_expiry_date: str | None = None
    option_chain_expiry_date: str | None = None

    def get_spot(self, symbol: str, exchange: str) -> SpotQuoteSnapshot:
        self.spot_exchange = exchange
        return SpotQuoteSnapshot(symbol=symbol, exchange=exchange, ltp=Decimal("24400"))

    def get_future(self, symbol: str, exchange: str, expiry_date: str) -> FutureQuoteSnapshot:
        self.future_exchange = exchange
        self.future_expiry_date = expiry_date
        return FutureQuoteSnapshot(
            symbol=symbol,
            exchange=exchange,
            underlying=symbol,
            expiry_date=expiry_date,
            ltp=Decimal("24450"),
        )

    def get_option_chain(self, underlying: str, exchange: str, expiry_date: str):
        self.option_chain_exchange = exchange
        self.option_chain_expiry_date = expiry_date
        return SimpleNamespace(
            underlying=underlying,
            exchange=exchange,
            expiry_date=expiry_date,
            spot_price=Decimal("24400"),
            atm_strike=Decimal("24400"),
            strikes=(),
        )

    def get_atm_strike(self, underlying: str, exchange: str, expiry_date: str) -> Decimal | None:
        return Decimal("24400")


class _FixedInstruments:
    def get_lot_size(self, underlying: str) -> int:
        return 75

    def get_tick_size(self, underlying: str) -> Decimal:
        return Decimal("0.05")

    def get_strike_interval(self, underlying: str) -> Decimal:
        return Decimal("50")


class _FixedExpiryCalendar:
    def calculate_dte(self, exchange: str, from_date: date, expiry_date: date) -> int:
        return max((expiry_date - from_date).days, 0)

    def calculate_tte_seconds(self, exchange: str, now: datetime, expiry_date: date) -> int:
        return 3600

    def nearest_monthly_expiry(self, underlying: str, exchange: str, on_date: date) -> date | None:
        """A monthly expiry ~3 weeks later than any weekly expiry these
        tests use, so option_expiry != future_expiry is always provable."""
        return on_date + timedelta(days=21)


class _AlwaysOpenMarketStatus:
    def is_market_open(self, exchange: str, moment: datetime) -> bool:
        return True

    def trade_date(self, exchange: str, moment: datetime) -> date:
        return moment.date()


def _build_factory(market_data: _RecordingMarketData) -> CalculationContextFactory:
    return CalculationContextFactory(
        market_data,
        _FixedInstruments(),
        ExpiryProvider(_FixedExpiryCalendar()),
        InterestRateProvider(),
        DividendProvider(),
        VolatilityProvider(),
        MarketStatusProvider(_AlwaysOpenMarketStatus(), TimeProvider()),
    )


def test_spot_lookup_uses_cash_exchange_not_option_contract_exchange() -> None:
    """get_spot() must be called with NSE even when the context is built for
    the NIFTY option chain on NFO; get_future()/get_option_chain() must keep
    the original NFO exchange."""
    market_data = _RecordingMarketData()
    factory = _build_factory(market_data)
    future_expiry = datetime.now(timezone.utc).date() + timedelta(days=7)

    factory.build("NIFTY", "NFO", future_expiry.strftime("%d-%b-%Y"))

    assert market_data.spot_exchange == "NSE"
    assert market_data.future_exchange == "NFO"
    assert market_data.option_chain_exchange == "NFO"


def test_spot_lookup_leaves_unrecognized_exchange_unchanged() -> None:
    """An exchange with no known cash mapping (e.g. already-cash NSE) must
    pass through unchanged rather than being altered unexpectedly."""
    market_data = _RecordingMarketData()
    factory = _build_factory(market_data)
    future_expiry = datetime.now(timezone.utc).date() + timedelta(days=7)

    factory.build("NIFTY", "NSE", future_expiry.strftime("%d-%b-%Y"))

    assert market_data.spot_exchange == "NSE"


class TestFutureExpiryIndependentOfOptionExpiry:
    """Task 10: get_future() must use the futures contract's own (monthly)
    expiry, not the weekly option-chain expiry the context was built for.
    Reusing the weekly expiry made every live futures lookup ask Breeze for
    a contract that doesn't exist (options are weekly, NIFTY futures are
    monthly) -- confirmed live: 'stock_code was not found in Breeze's own
    scrip dictionary'."""

    def test_future_lookup_uses_monthly_expiry_not_option_weekly_expiry(self) -> None:
        market_data = _RecordingMarketData()
        factory = _build_factory(market_data)
        option_expiry = datetime.now(timezone.utc).date() + timedelta(days=7)
        today = datetime.now(timezone.utc).date()

        factory.build("NIFTY", "NFO", option_expiry.strftime("%d-%b-%Y"))

        assert market_data.option_chain_expiry_date == option_expiry.strftime("%d-%b-%Y")
        assert market_data.future_expiry_date != market_data.option_chain_expiry_date
        # _FixedExpiryCalendar.nearest_monthly_expiry() resolves off trade_date
        # (today), independent of whatever weekly option_expiry was requested.
        assert market_data.future_expiry_date == (today + timedelta(days=21)).strftime("%d-%b-%Y")

    def test_future_lookup_recalculates_from_live_monthly_resolution_each_call(self) -> None:
        """Dynamic rollover: as the resolved monthly contract changes (e.g.
        crossing a month boundary between calculation cycles), get_future()
        must receive the newly resolved value each time -- never a cached or
        hardcoded expiry from an earlier call."""

        class _RollingMonthlyCalendar(_FixedExpiryCalendar):
            def __init__(self) -> None:
                self.calls = 0

            def nearest_monthly_expiry(
                self, underlying: str, exchange: str, on_date: date
            ) -> date | None:
                self.calls += 1
                # Simulate the monthly contract rolling over between cycles.
                return on_date + timedelta(days=21 if self.calls == 1 else 49)

        calendar = _RollingMonthlyCalendar()
        market_data = _RecordingMarketData()
        factory = CalculationContextFactory(
            market_data,
            _FixedInstruments(),
            ExpiryProvider(calendar),
            InterestRateProvider(),
            DividendProvider(),
            VolatilityProvider(),
            MarketStatusProvider(_AlwaysOpenMarketStatus(), TimeProvider()),
        )
        option_expiry = datetime.now(timezone.utc).date() + timedelta(days=7)

        factory.build("NIFTY", "NFO", option_expiry.strftime("%d-%b-%Y"))
        first_future_expiry = market_data.future_expiry_date

        factory.build("NIFTY", "NFO", option_expiry.strftime("%d-%b-%Y"))
        rolled_future_expiry = market_data.future_expiry_date

        assert calendar.calls == 2  # resolved fresh on every context build, not cached
        assert rolled_future_expiry != first_future_expiry

    def test_future_lookup_falls_back_to_option_expiry_when_no_monthly_expiry_exists(
        self,
    ) -> None:
        """An underlying with no futures market (nearest_monthly_expiry()
        returns None) must not crash the whole context -- falls back to the
        option expiry, matching behavior before this fix existed."""

        class _NoMonthlyExpiryCalendar(_FixedExpiryCalendar):
            def nearest_monthly_expiry(
                self, underlying: str, exchange: str, on_date: date
            ) -> date | None:
                return None

        market_data = _RecordingMarketData()
        factory = CalculationContextFactory(
            market_data,
            _FixedInstruments(),
            ExpiryProvider(_NoMonthlyExpiryCalendar()),
            InterestRateProvider(),
            DividendProvider(),
            VolatilityProvider(),
            MarketStatusProvider(_AlwaysOpenMarketStatus(), TimeProvider()),
        )
        option_expiry = datetime.now(timezone.utc).date() + timedelta(days=7)

        factory.build("NIFTY", "NFO", option_expiry.strftime("%d-%b-%Y"))

        assert market_data.future_expiry_date == option_expiry.strftime("%d-%b-%Y")
