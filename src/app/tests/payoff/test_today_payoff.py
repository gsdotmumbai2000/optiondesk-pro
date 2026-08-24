"""Tests for today's (time-decayed) payoff analytics: cross-checked
directly against BlackScholesEngine.price(), the same reference the
production code itself calls.
"""

import dataclasses
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
from app.payoff.analytics.expiry_payoff import total_expiry_pnl
from app.payoff.analytics.payoff_curve import build_payoff_curve
from app.payoff.analytics.today_payoff import build_today_curve, leg_today_pnl, total_today_pnl
from app.payoff.models.legs import StrategyLeg
from app.pricing.black_scholes.engine import BlackScholesEngine
from app.pricing.models.enums import OptionType
from app.pricing.models.option_contract import OptionContract

# --- Fixture pattern reused from test_bs_greeks.py / test_payoff_calculator.py ---


class _FixedMarketData:
    def __init__(self, spot: Decimal) -> None:
        self._spot = spot

    def get_spot(self, symbol: str, exchange: str):
        return SimpleNamespace(symbol=symbol, exchange=exchange, ltp=self._spot)

    def get_future(self, symbol: str, exchange: str, expiry_date: str):
        return SimpleNamespace(
            symbol=symbol, exchange=exchange, underlying=symbol,
            expiry_date=expiry_date, ltp=self._spot,
        )

    def get_option_chain(self, underlying: str, exchange: str, expiry_date: str):
        return SimpleNamespace(
            underlying=underlying, exchange=exchange, expiry_date=expiry_date,
            spot_price=self._spot, atm_strike=self._spot, strikes=(),
        )

    def get_atm_strike(self, underlying: str, exchange: str, expiry_date: str):
        return self._spot


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
        return 365 * 24 * 3600  # exactly 1 year, for clean reference-value math

    def nearest_monthly_expiry(self, underlying: str, exchange: str, on_date: date):
        return on_date + timedelta(days=365)


class _AlwaysOpenMarketStatus:
    def is_market_open(self, exchange: str, moment: datetime) -> bool:
        return True

    def trade_date(self, exchange: str, moment: datetime) -> date:
        return moment.date()


def _context(
    spot: Decimal,
    *,
    rate: Decimal = Decimal("0.05"),
    volatility: Decimal = Decimal("0.20"),
) -> CalculationContext:
    """A real CalculationContext with exactly 1 year to expiry."""
    factory = CalculationContextFactory(
        _FixedMarketData(spot),
        _FixedInstruments(),
        ExpiryProvider(_FixedExpiryCalendar()),
        InterestRateProvider(risk_free_rate=rate),
        DividendProvider(),
        VolatilityProvider(volatility=volatility),
        MarketStatusProvider(_AlwaysOpenMarketStatus(), TimeProvider()),
    )
    return factory.build(
        "NIFTY", "NFO",
        (datetime.now(timezone.utc).date() + timedelta(days=365)).strftime("%d-%b-%Y"),
    )


def _leg(option_type: OptionType, quantity: int, strike: Decimal, premium: Decimal) -> StrategyLeg:
    return StrategyLeg(
        strike=strike, option_type=option_type, quantity=quantity, premium=premium, expiry=date(2027, 1, 1),
    )


class TestLegTodayPnlMatchesEngineDirectly:
    def test_single_long_call_matches_black_scholes_engine(self) -> None:
        leg = _leg(OptionType.CALL, 1, Decimal("100"), Decimal("5"))
        ctx = _context(Decimal("100"))

        result = leg_today_pnl(Decimal("105"), leg, ctx)

        variant = dataclasses.replace(ctx, spot_price=Decimal("105"))
        contract = OptionContract(strike=leg.strike, option_type=leg.option_type, expiry=leg.expiry, multiplier=1)
        expected_price = BlackScholesEngine().price(variant, contract).theoretical_price
        assert result == expected_price - leg.premium

    def test_quantity_and_multiplier_scale_the_result(self) -> None:
        leg = _leg(OptionType.CALL, 1, Decimal("100"), Decimal("5"))
        scaled_leg = StrategyLeg(
            strike=leg.strike, option_type=leg.option_type, quantity=3, premium=leg.premium,
            expiry=leg.expiry, multiplier=2,
        )
        ctx = _context(Decimal("100"))

        single = leg_today_pnl(Decimal("105"), leg, ctx)
        scaled = leg_today_pnl(Decimal("105"), scaled_leg, ctx)

        assert scaled == single * 6


class TestTotalTodayPnl:
    def test_sums_across_legs(self) -> None:
        legs = (
            _leg(OptionType.CALL, 1, Decimal("100"), Decimal("5")),
            _leg(OptionType.CALL, -1, Decimal("110"), Decimal("2")),
        )
        ctx = _context(Decimal("105"))

        total = total_today_pnl(Decimal("105"), legs, ctx)
        manual = sum(leg_today_pnl(Decimal("105"), leg, ctx) for leg in legs)

        assert total == manual

    def test_empty_legs_returns_zero(self) -> None:
        assert total_today_pnl(Decimal("100"), (), _context(Decimal("100"))) == Decimal("0")

    def test_has_positive_extrinsic_value_versus_expiry_pnl(self) -> None:
        """With a full year to expiry, an ATM long call's today value must
        exceed its (zero) intrinsic expiry value -- pure time value."""
        legs = (_leg(OptionType.CALL, 1, Decimal("100"), Decimal("0")),)
        ctx = _context(Decimal("100"))

        today = total_today_pnl(Decimal("100"), legs, ctx)
        expiry = total_expiry_pnl(Decimal("100"), legs)

        assert today > expiry == Decimal("0")


class TestBuildTodayCurve:
    def test_shares_price_bounds_with_expiry_curve(self) -> None:
        legs = (_leg(OptionType.CALL, 1, Decimal("100"), Decimal("5")),
                _leg(OptionType.PUT, 1, Decimal("90"), Decimal("3")))
        ctx = _context(Decimal("100"))

        today_curve = build_today_curve(legs, ctx)
        expiry_curve = build_payoff_curve(legs, ctx)

        assert today_curve.points[0].underlying_price == expiry_curve.points[0].underlying_price
        assert today_curve.points[-1].underlying_price == expiry_curve.points[-1].underlying_price
        assert len(today_curve.points) == len(expiry_curve.points)

    def test_each_point_matches_total_today_pnl_at_that_price(self) -> None:
        legs = (_leg(OptionType.CALL, 1, Decimal("100"), Decimal("5")),)
        ctx = _context(Decimal("100"))

        curve = build_today_curve(legs, ctx, samples=7)

        for point in curve.points:
            assert point.pnl == total_today_pnl(point.underlying_price, legs, ctx)

    def test_empty_legs_returns_empty_curve(self) -> None:
        assert build_today_curve((), _context(Decimal("100"))).points == ()

    def test_samples_below_two_returns_empty_curve(self) -> None:
        legs = (_leg(OptionType.CALL, 1, Decimal("100"), Decimal("5")),)
        assert build_today_curve(legs, _context(Decimal("100")), samples=1).points == ()


class TestPerLegMarketVolatility:
    """When the context carries a live option chain, each leg must be
    repriced at its own strike's live IV -- not one shared context.volatility
    across every strike -- since real strikes carry different market IV
    (skew). These are the cases the other tests in this file can't cover:
    their fixture chain always has strikes=(), which only exercises the
    context.volatility fallback path.
    """

    def test_leg_uses_its_strike_quoted_iv_not_the_flat_context_volatility(self) -> None:
        leg = _leg(OptionType.CALL, 1, Decimal("110"), Decimal("5"))
        ctx = _context(Decimal("100"))  # context.volatility defaults to 0.20
        chain = OptionChainSnapshot(
            underlying="NIFTY", exchange="NFO", expiry_date="01-Jan-2027",
            spot_price=Decimal("100"), atm_strike=Decimal("100"),
            strikes=(OptionStrikeSnapshot(strike_price=Decimal("110"), call_iv=Decimal("0.35")),),
        )
        ctx_with_chain = dataclasses.replace(ctx, option_chain_snapshot=chain)

        result = leg_today_pnl(Decimal("105"), leg, ctx_with_chain)

        variant_at_flat_vol = dataclasses.replace(ctx, spot_price=Decimal("105"))
        contract = OptionContract(strike=leg.strike, option_type=leg.option_type, expiry=leg.expiry, multiplier=1)
        flat_vol_price = BlackScholesEngine().price(variant_at_flat_vol, contract).theoretical_price
        variant_at_quoted_iv = dataclasses.replace(ctx, spot_price=Decimal("105"), volatility=Decimal("0.35"))
        quoted_iv_price = BlackScholesEngine().price(variant_at_quoted_iv, contract).theoretical_price

        assert result == quoted_iv_price - leg.premium
        assert result != flat_vol_price - leg.premium

    def test_two_legs_at_different_strikes_use_different_quoted_ivs(self) -> None:
        """The core bug being fixed: a strangle's call and put strikes must
        not be flattened to the same volatility."""
        call_leg = _leg(OptionType.CALL, -1, Decimal("110"), Decimal("2"))
        put_leg = _leg(OptionType.PUT, -1, Decimal("90"), Decimal("2"))
        ctx = _context(Decimal("100"))
        chain = OptionChainSnapshot(
            underlying="NIFTY", exchange="NFO", expiry_date="01-Jan-2027",
            spot_price=Decimal("100"), atm_strike=Decimal("100"),
            strikes=(
                OptionStrikeSnapshot(strike_price=Decimal("110"), call_iv=Decimal("0.15")),
                OptionStrikeSnapshot(strike_price=Decimal("90"), put_iv=Decimal("0.40")),
            ),
        )
        ctx_with_chain = dataclasses.replace(ctx, option_chain_snapshot=chain)

        call_result = leg_today_pnl(Decimal("100"), call_leg, ctx_with_chain)
        put_result = leg_today_pnl(Decimal("100"), put_leg, ctx_with_chain)

        contract_call = OptionContract(strike=call_leg.strike, option_type=OptionType.CALL, expiry=call_leg.expiry, multiplier=1)
        contract_put = OptionContract(strike=put_leg.strike, option_type=OptionType.PUT, expiry=put_leg.expiry, multiplier=1)
        expected_call_price = BlackScholesEngine().price(
            dataclasses.replace(ctx, spot_price=Decimal("100"), volatility=Decimal("0.15")), contract_call,
        ).theoretical_price
        expected_put_price = BlackScholesEngine().price(
            dataclasses.replace(ctx, spot_price=Decimal("100"), volatility=Decimal("0.40")), contract_put,
        ).theoretical_price
        assert call_result == -(expected_call_price - call_leg.premium)
        assert put_result == -(expected_put_price - put_leg.premium)

    def test_solves_from_live_ltp_when_no_quoted_iv_is_published(self) -> None:
        leg = _leg(OptionType.CALL, 1, Decimal("110"), Decimal("5"))
        ctx = _context(Decimal("100"))
        contract = OptionContract(strike=leg.strike, option_type=leg.option_type, expiry=leg.expiry, multiplier=1)
        live_price = BlackScholesEngine().price(
            dataclasses.replace(ctx, volatility=Decimal("0.28")), contract,
        ).theoretical_price
        chain = OptionChainSnapshot(
            underlying="NIFTY", exchange="NFO", expiry_date="01-Jan-2027",
            spot_price=Decimal("100"), atm_strike=Decimal("100"),
            strikes=(OptionStrikeSnapshot(strike_price=Decimal("110"), call_ltp=live_price),),
        )
        ctx_with_chain = dataclasses.replace(ctx, option_chain_snapshot=chain)

        result = leg_today_pnl(Decimal("100"), leg, ctx_with_chain)

        assert abs(result - (live_price - leg.premium)) < Decimal("0.01")

    def test_falls_back_to_flat_volatility_when_strike_not_in_chain(self) -> None:
        leg = _leg(OptionType.CALL, 1, Decimal("110"), Decimal("5"))
        ctx = _context(Decimal("100"))
        chain = OptionChainSnapshot(
            underlying="NIFTY", exchange="NFO", expiry_date="01-Jan-2027",
            spot_price=Decimal("100"), atm_strike=Decimal("100"),
            strikes=(OptionStrikeSnapshot(strike_price=Decimal("120"), call_iv=Decimal("0.35")),),
        )
        ctx_with_chain = dataclasses.replace(ctx, option_chain_snapshot=chain)

        with_chain = leg_today_pnl(Decimal("105"), leg, ctx_with_chain)
        without_chain = leg_today_pnl(Decimal("105"), leg, ctx)

        assert with_chain == without_chain

    def test_live_pnl_at_current_spot_reflects_real_drift_not_tautological_zero(self) -> None:
        """Regression guard: an earlier version of this fix solved IV from
        the leg's own *stored* premium anchored at the current spot, which
        made today's PnL exactly zero at the current spot no matter how far
        the underlying had actually moved since entry. Using the chain's
        live quote instead must NOT have that problem: a call bought for 5
        that's now deep OTM (live price far below 5) must show a real loss
        at today's actual spot, not zero."""
        leg = _leg(OptionType.CALL, 1, Decimal("150"), Decimal("5"))
        ctx = _context(Decimal("80"))  # spot has since fallen well below the strike
        chain = OptionChainSnapshot(
            underlying="NIFTY", exchange="NFO", expiry_date="01-Jan-2027",
            spot_price=Decimal("80"), atm_strike=Decimal("80"),
            strikes=(OptionStrikeSnapshot(strike_price=Decimal("150"), call_iv=Decimal("0.20")),),
        )
        ctx_with_chain = dataclasses.replace(ctx, option_chain_snapshot=chain)

        result = leg_today_pnl(Decimal("80"), leg, ctx_with_chain)

        assert result < Decimal("-4")  # option is now worth close to nothing
