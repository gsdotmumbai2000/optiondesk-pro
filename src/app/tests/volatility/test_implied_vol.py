"""Tests for resolve_implied_volatility, including the Black-Scholes
inversion fallback added to replace the previous hardcoded 0.20 default.
"""

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.factory.context_factory import CalculationContextFactory
from app.calculation.models.snapshots import OptionChainSnapshot, OptionStrikeSnapshot
from app.calculation.providers.dividend_provider import DividendProvider
from app.calculation.providers.expiry_provider import ExpiryProvider
from app.calculation.providers.interest_rate_provider import InterestRateProvider
from app.calculation.providers.market_status_provider import MarketStatusProvider
from app.calculation.providers.time_provider import TimeProvider
from app.calculation.providers.volatility_provider import VolatilityProvider
from app.pricing.black_scholes import formulas
from app.pricing.models.enums import OptionType
from app.volatility.analytics.implied_vol import resolve_implied_volatility


# --- Fixture pattern reused from test_active_strategy_pipeline.py ---


class _RecordingMarketData:
    def get_spot(self, symbol: str, exchange: str):
        return SimpleNamespace(symbol=symbol, exchange=exchange, ltp=Decimal("24500"))

    def get_future(self, symbol: str, exchange: str, expiry_date: str):
        return SimpleNamespace(
            symbol=symbol, exchange=exchange, underlying=symbol,
            expiry_date=expiry_date, ltp=Decimal("24550"),
        )

    def get_option_chain(self, underlying: str, exchange: str, expiry_date: str):
        return SimpleNamespace(
            underlying=underlying, exchange=exchange, expiry_date=expiry_date,
            spot_price=Decimal("24500"), atm_strike=Decimal("24500"), strikes=(),
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


class _FixedExpiryCalendar:
    def calculate_dte(self, exchange: str, from_date: date, expiry_date: date) -> int:
        return max((expiry_date - from_date).days, 0)

    def calculate_tte_seconds(self, exchange: str, now: datetime, expiry_date: date) -> int:
        return 3600

    def nearest_monthly_expiry(self, underlying: str, exchange: str, on_date: date):
        return on_date + timedelta(days=21)


class _AlwaysOpenMarketStatus:
    def is_market_open(self, exchange: str, moment: datetime) -> bool:
        return True

    def trade_date(self, exchange: str, moment: datetime) -> date:
        return moment.date()


def _context_with_no_quoted_volatility() -> CalculationContext:
    """A real CalculationContext with no context-level volatility/implied
    volatility set, so resolve_implied_volatility must fall through to the
    option chain."""
    factory = CalculationContextFactory(
        _RecordingMarketData(),
        _FixedInstruments(),
        ExpiryProvider(_FixedExpiryCalendar()),
        InterestRateProvider(),
        DividendProvider(),
        VolatilityProvider(),
        MarketStatusProvider(_AlwaysOpenMarketStatus(), TimeProvider()),
    )
    option_expiry = datetime.now(timezone.utc).date() + timedelta(days=7)
    context = factory.build("NIFTY", "NFO", option_expiry.strftime("%d-%b-%Y"))
    return replace(context, volatility=Decimal("0"), implied_volatility=None)


def _price_at(strike: float, volatility: float, option_type: OptionType, context: CalculationContext) -> Decimal:
    spot = float(context.spot_price)
    rate = float(context.risk_free_rate)
    dividend = float(context.dividend_yield)
    time_to_expiry = float(context.time_to_expiry)
    d1_value = formulas.d1(spot, strike, rate, dividend, volatility, time_to_expiry)
    d2_value = formulas.d2(d1_value, volatility, time_to_expiry)
    if option_type == OptionType.CALL:
        price = formulas.call_price(spot, strike, rate, dividend, time_to_expiry, d1_value, d2_value)
    else:
        price = formulas.put_price(spot, strike, rate, dividend, time_to_expiry, d1_value, d2_value)
    # Not rounded to a quote-realistic 2-4dp: the fixture context's fake
    # expiry calendar gives an unrealistically tiny time_to_expiry (~1 hour),
    # which makes deep-OTM prices sub-paisa; full precision keeps the
    # round-trip solvable without changing what's being tested.
    return Decimal(str(price))


def _empty_chain(context: CalculationContext) -> OptionChainSnapshot:
    return OptionChainSnapshot(
        underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026",
        spot_price=context.spot_price, atm_strike=context.atm_strike, strikes=(),
    )


class TestContextLevelVolatilityTakesPriority:
    def test_context_implied_volatility_is_returned_directly(self) -> None:
        context = _context_with_no_quoted_volatility()
        context = replace(context, implied_volatility=Decimal("0.33"))
        chain = _empty_chain(context)

        assert resolve_implied_volatility(context, chain) == Decimal("0.33")

    def test_context_volatility_is_returned_when_no_implied_set(self) -> None:
        context = _context_with_no_quoted_volatility()
        context = replace(context, volatility=Decimal("0.18"))
        chain = _empty_chain(context)

        assert resolve_implied_volatility(context, chain) == Decimal("0.18")


class TestQuotedChainIvTakesPriorityOverSolving:
    def test_atm_quoted_call_iv_is_returned_without_solving(self) -> None:
        context = _context_with_no_quoted_volatility()
        strike = OptionStrikeSnapshot(
            strike_price=context.atm_strike, call_iv=Decimal("0.19"), is_atm=True,
        )
        chain = OptionChainSnapshot(
            underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026",
            spot_price=context.spot_price, atm_strike=context.atm_strike, strikes=(strike,),
        )

        assert resolve_implied_volatility(context, chain) == Decimal("0.19")


class TestSolvesFromTradedPriceWhenNoQuotedIv:
    def test_atm_strike_solves_iv_from_call_ltp(self) -> None:
        context = _context_with_no_quoted_volatility()
        known_vol = 0.21
        strike_price = context.atm_strike
        call_ltp = _price_at(float(strike_price), known_vol, OptionType.CALL, context)
        strike = OptionStrikeSnapshot(strike_price=strike_price, call_ltp=call_ltp, is_atm=True)
        chain = OptionChainSnapshot(
            underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026",
            spot_price=context.spot_price, atm_strike=context.atm_strike, strikes=(strike,),
        )

        resolved = resolve_implied_volatility(context, chain)

        assert abs(float(resolved) - known_vol) < 1e-3

    def test_atm_strike_solves_iv_from_put_ltp_when_no_call_ltp(self) -> None:
        context = _context_with_no_quoted_volatility()
        known_vol = 0.27
        strike_price = context.atm_strike
        put_ltp = _price_at(float(strike_price), known_vol, OptionType.PUT, context)
        strike = OptionStrikeSnapshot(strike_price=strike_price, put_ltp=put_ltp, is_atm=True)
        chain = OptionChainSnapshot(
            underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026",
            spot_price=context.spot_price, atm_strike=context.atm_strike, strikes=(strike,),
        )

        resolved = resolve_implied_volatility(context, chain)

        assert abs(float(resolved) - known_vol) < 1e-3

    def test_non_atm_strike_solves_iv_from_ltp_when_no_iv_anywhere(self) -> None:
        """No ATM strike present at all -- falls through to the final
        any-strike solve pass, not the flat 0.20 default."""
        context = _context_with_no_quoted_volatility()
        known_vol = 0.31
        off_strike = context.atm_strike + Decimal("500")
        call_ltp = _price_at(float(off_strike), known_vol, OptionType.CALL, context)
        strike = OptionStrikeSnapshot(strike_price=off_strike, call_ltp=call_ltp, is_atm=False)
        chain = OptionChainSnapshot(
            underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026",
            spot_price=context.spot_price, atm_strike=context.atm_strike, strikes=(strike,),
        )

        resolved = resolve_implied_volatility(context, chain)

        assert abs(float(resolved) - known_vol) < 1e-3


class TestFallsBackToFlatVolatilityOnlyWhenNoDataAtAll:
    def test_empty_chain_and_no_context_volatility_returns_flat_default(self) -> None:
        context = _context_with_no_quoted_volatility()
        chain = _empty_chain(context)

        assert resolve_implied_volatility(context, chain) == Decimal("0.20")

    def test_strike_with_no_iv_and_no_ltp_falls_back_to_flat_default(self) -> None:
        context = _context_with_no_quoted_volatility()
        strike = OptionStrikeSnapshot(strike_price=context.atm_strike, is_atm=True)
        chain = OptionChainSnapshot(
            underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026",
            spot_price=context.spot_price, atm_strike=context.atm_strike, strikes=(strike,),
        )

        assert resolve_implied_volatility(context, chain) == Decimal("0.20")
