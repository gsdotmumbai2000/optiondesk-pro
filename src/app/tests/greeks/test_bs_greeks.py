"""Tests for calculate_bs_greeks() against an independently-implemented
reference (textbook Black-Scholes Greek formulas, recomputed from scratch
here rather than reusing app.pricing.black_scholes), plus invariants that
must hold for any valid input regardless of the specific numbers.
"""

import math
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.factory.context_factory import CalculationContextFactory
from app.calculation.providers.dividend_provider import DividendProvider
from app.calculation.providers.expiry_provider import ExpiryProvider
from app.calculation.providers.interest_rate_provider import InterestRateProvider
from app.calculation.providers.market_status_provider import MarketStatusProvider
from app.calculation.providers.time_provider import TimeProvider
from app.calculation.providers.volatility_provider import VolatilityProvider
from app.greeks.analytics.bs_greeks import calculate_bs_greeks
from app.pricing.black_scholes.engine import BlackScholesEngine
from app.pricing.models.enums import ExerciseStyle, OptionType
from app.pricing.models.option_contract import OptionContract


# --- Fixture pattern reused from test_active_strategy_pipeline.py ---


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
    *,
    spot: Decimal = Decimal("100"),
    rate: Decimal = Decimal("0.05"),
    volatility: Decimal = Decimal("0.20"),
) -> CalculationContext:
    """A real CalculationContext with exactly 1 year to expiry, so the
    reference-value math above (T=1) is exact rather than approximate."""
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


def _contract(strike: Decimal, option_type: OptionType, *, multiplier: int = 1) -> OptionContract:
    return OptionContract(strike=strike, option_type=option_type, expiry=date(2027, 1, 1), multiplier=multiplier)


def _reference_greeks(
    spot: float, strike: float, rate: float, dividend: float, vol: float, t: float, option_type: OptionType,
) -> dict[str, float]:
    """Independent from-scratch Black-Scholes Greeks, using math.erf for the
    normal CDF/PDF rather than app.pricing.black_scholes.distribution --
    this must never import from app.pricing or app.greeks."""
    def cdf(x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    def pdf(x: float) -> float:
        return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

    d1 = (math.log(spot / strike) + (rate - dividend + 0.5 * vol * vol) * t) / (vol * math.sqrt(t))
    d2 = d1 - vol * math.sqrt(t)
    sqrt_t = math.sqrt(t)
    growth = math.exp(-dividend * t)
    discount = math.exp(-rate * t)
    pdf_d1 = pdf(d1)

    gamma = pdf_d1 / (spot * vol * sqrt_t) * growth
    vega_raw = spot * growth * pdf_d1 * sqrt_t

    if option_type == OptionType.CALL:
        delta = cdf(d1) * growth
        theta_annual = (
            -spot * growth * pdf_d1 * vol / (2 * sqrt_t)
            - rate * strike * discount * cdf(d2)
            + dividend * spot * growth * cdf(d1)
        )
        rho = strike * t * discount * cdf(d2)
    else:
        delta = (cdf(d1) - 1.0) * growth
        theta_annual = (
            -spot * growth * pdf_d1 * vol / (2 * sqrt_t)
            + rate * strike * discount * cdf(-d2)
            - dividend * spot * growth * cdf(-d1)
        )
        rho = -strike * t * discount * cdf(-d2)

    # Production reports theta per calendar day and vega per 1% vol move,
    # not the raw per-year / per-100%-vol textbook derivatives -- see
    # app/greeks/analytics/bs_greeks.py.
    theta = theta_annual / 365.0
    vega = vega_raw / 100.0

    return {"delta": delta, "gamma": gamma, "theta": theta, "vega": vega, "rho": rho}


def _actual_greeks(context: CalculationContext, contract: OptionContract):
    pricing = BlackScholesEngine().price(context, contract)
    return calculate_bs_greeks(context, contract, pricing)


class TestMatchesIndependentReferenceFormula:
    """(context, strike, option_type) triples covering ATM/ITM/OTM x call/put."""

    @pytest.mark.parametrize(
        "strike,option_type",
        [
            (Decimal("100"), OptionType.CALL),
            (Decimal("100"), OptionType.PUT),
            (Decimal("110"), OptionType.CALL),  # OTM call
            (Decimal("110"), OptionType.PUT),   # ITM put
            (Decimal("90"), OptionType.CALL),   # ITM call
            (Decimal("90"), OptionType.PUT),    # OTM put
        ],
    )
    def test_greeks_match_reference_within_tolerance(self, strike: Decimal, option_type: OptionType) -> None:
        context = _context()
        contract = _contract(strike, option_type)

        actual = _actual_greeks(context, contract)
        expected = _reference_greeks(
            100.0, float(strike), 0.05, 0.0, 0.20, float(context.time_to_expiry), option_type,
        )

        assert float(actual.delta) == pytest.approx(expected["delta"], abs=1e-4)
        assert float(actual.gamma) == pytest.approx(expected["gamma"], abs=1e-4)
        assert float(actual.theta) == pytest.approx(expected["theta"], rel=1e-3)
        assert float(actual.vega) == pytest.approx(expected["vega"], rel=1e-3)
        assert float(actual.rho) == pytest.approx(expected["rho"], rel=1e-3)


class TestPutCallParityInvariants:
    """These hold for ANY valid Black-Scholes inputs -- not tied to a
    specific reference number, so they catch a broader class of bugs."""

    def test_call_minus_put_delta_equals_dividend_discount_factor(self) -> None:
        context = _context()
        call = _actual_greeks(context, _contract(Decimal("105"), OptionType.CALL))
        put = _actual_greeks(context, _contract(Decimal("105"), OptionType.PUT))

        assert float(call.delta - put.delta) == pytest.approx(1.0, abs=1e-4)  # q=0 here

    def test_gamma_identical_for_call_and_put_at_same_strike(self) -> None:
        context = _context()
        call = _actual_greeks(context, _contract(Decimal("105"), OptionType.CALL))
        put = _actual_greeks(context, _contract(Decimal("105"), OptionType.PUT))

        assert float(call.gamma) == pytest.approx(float(put.gamma), abs=1e-9)

    def test_vega_identical_for_call_and_put_at_same_strike(self) -> None:
        context = _context()
        call = _actual_greeks(context, _contract(Decimal("105"), OptionType.CALL))
        put = _actual_greeks(context, _contract(Decimal("105"), OptionType.PUT))

        assert float(call.vega) == pytest.approx(float(put.vega), abs=1e-9)

    def test_call_delta_bounded_zero_to_one(self) -> None:
        context = _context()
        for strike in (Decimal("50"), Decimal("100"), Decimal("150")):
            call = _actual_greeks(context, _contract(strike, OptionType.CALL))
            assert Decimal("0") <= call.delta <= Decimal("1")

    def test_put_delta_bounded_negative_one_to_zero(self) -> None:
        context = _context()
        for strike in (Decimal("50"), Decimal("100"), Decimal("150")):
            put = _actual_greeks(context, _contract(strike, OptionType.PUT))
            assert Decimal("-1") <= put.delta <= Decimal("0")

    def test_gamma_and_vega_always_non_negative(self) -> None:
        context = _context()
        for strike in (Decimal("50"), Decimal("100"), Decimal("150")):
            for option_type in (OptionType.CALL, OptionType.PUT):
                greeks = _actual_greeks(context, _contract(strike, option_type))
                assert greeks.gamma >= 0
                assert greeks.vega >= 0

    def test_call_delta_monotonically_decreases_as_strike_increases(self) -> None:
        context = _context()
        strikes = [Decimal("80"), Decimal("90"), Decimal("100"), Decimal("110"), Decimal("120")]
        deltas = [_actual_greeks(context, _contract(k, OptionType.CALL)).delta for k in strikes]

        assert deltas == sorted(deltas, reverse=True)

    def test_gamma_peaks_near_the_money(self) -> None:
        context = _context()
        atm_gamma = _actual_greeks(context, _contract(Decimal("100"), OptionType.CALL)).gamma
        deep_otm_gamma = _actual_greeks(context, _contract(Decimal("200"), OptionType.CALL)).gamma
        deep_itm_gamma = _actual_greeks(context, _contract(Decimal("20"), OptionType.CALL)).gamma

        assert atm_gamma > deep_otm_gamma
        assert atm_gamma > deep_itm_gamma


class TestDegenerateCases:
    """calculate_bs_greeks()'s explicit zero-guard for T<=0 or vol<=0."""

    def test_zero_time_to_expiry_returns_all_zeros(self) -> None:
        context = replace(_context(), time_to_expiry=Decimal("0"))
        greeks = calculate_bs_greeks(context, _contract(Decimal("100"), OptionType.CALL), _dummy_pricing())

        assert greeks.delta == 0
        assert greeks.gamma == 0
        assert greeks.theta == 0
        assert greeks.vega == 0
        assert greeks.rho == 0
        assert greeks.vanna == 0
        assert greeks.charm == 0
        assert greeks.vomma == 0

    def test_zero_volatility_returns_all_zeros(self) -> None:
        context = replace(_context(), volatility=Decimal("0"))
        greeks = calculate_bs_greeks(context, _contract(Decimal("100"), OptionType.CALL), _dummy_pricing())

        assert greeks.delta == 0
        assert greeks.gamma == 0


class TestMultiplierScaling:
    def test_multiplier_scales_all_greeks_linearly(self) -> None:
        context = _context()
        base = _actual_greeks(context, _contract(Decimal("100"), OptionType.CALL, multiplier=1))
        scaled = _actual_greeks(context, _contract(Decimal("100"), OptionType.CALL, multiplier=75))

        assert float(scaled.delta) == pytest.approx(float(base.delta) * 75, rel=1e-6)
        assert float(scaled.gamma) == pytest.approx(float(base.gamma) * 75, rel=1e-6)
        assert float(scaled.vega) == pytest.approx(float(base.vega) * 75, rel=1e-6)


class TestThetaVegaTraderScaling:
    """theta/vega must be the conventional trader-facing units (per
    calendar day / per 1% vol), not the raw per-year / per-100%-vol
    textbook derivatives -- confirmed against a real live NIFTY option
    where the raw annualized theta (~-11,067) was nonsensical next to the
    real ~-30/day decay a trader would recognize.
    """

    def test_theta_equals_raw_annualized_theta_over_365(self) -> None:
        """Computes the raw (unscaled) annualized theta independently --
        not via _reference_greeks, which already bakes in the /365 -- to
        directly prove the specific division factor, not just "matches
        the reference helper" (which would pass even if both sides shared
        a wrong factor)."""
        context = _context()
        contract = _contract(Decimal("100"), OptionType.CALL)
        spot, strike, rate, dividend, vol = 100.0, 100.0, 0.05, 0.0, 0.20
        t = float(context.time_to_expiry)

        def cdf(x: float) -> float:
            return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

        def pdf(x: float) -> float:
            return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

        d1 = (math.log(spot / strike) + (rate - dividend + 0.5 * vol * vol) * t) / (vol * math.sqrt(t))
        d2 = d1 - vol * math.sqrt(t)
        raw_theta_annual = (
            -spot * pdf(d1) * vol / (2 * math.sqrt(t)) - rate * strike * math.exp(-rate * t) * cdf(d2)
        )

        actual = _actual_greeks(context, contract)

        assert float(actual.theta) == pytest.approx(raw_theta_annual / 365.0, rel=1e-3)

    def test_short_dated_theta_is_a_realistic_small_number_not_thousands(self) -> None:
        """Regression guard for the exact real-world scenario that exposed
        the bug: a 2-day-to-expiry near-ATM option's daily theta should be
        a two- or three-digit number (per unit, before lot size), never
        the four/five-digit annualized figure the old code produced."""
        context = replace(_context(), time_to_expiry=Decimal("2") / Decimal("365"))
        contract = _contract(Decimal("100"), OptionType.CALL)

        greeks = _actual_greeks(context, contract)

        assert abs(float(greeks.theta)) < 50

    def test_vega_equals_raw_vega_over_100(self) -> None:
        """Same independent-derivation approach as the theta test above,
        to directly prove the /100 factor."""
        context = _context()
        contract = _contract(Decimal("100"), OptionType.CALL)
        spot, strike, rate, dividend, vol = 100.0, 100.0, 0.05, 0.0, 0.20
        t = float(context.time_to_expiry)

        def pdf(x: float) -> float:
            return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

        d1 = (math.log(spot / strike) + (rate - dividend + 0.5 * vol * vol) * t) / (vol * math.sqrt(t))
        raw_vega = spot * pdf(d1) * math.sqrt(t)

        actual = _actual_greeks(context, contract)

        assert float(actual.vega) == pytest.approx(raw_vega / 100.0, rel=1e-3)


def _dummy_pricing():
    from app.pricing.models.pricing_result import PricingResult

    return PricingResult(
        theoretical_price=Decimal("0"), intrinsic_value=Decimal("0"), extrinsic_value=Decimal("0"),
        d1=Decimal("0"), d2=Decimal("0"), forward_price=Decimal("0"), discount_factor=Decimal("1"),
        calculation_time=datetime.now(timezone.utc),
    )
