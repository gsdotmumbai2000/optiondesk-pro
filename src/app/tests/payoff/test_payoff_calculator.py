"""Engine-level wiring tests for PayoffCalculator: proves current_pnl,
expiry_pnl, max_gain/loss, breakevens, and future_value are all derived
consistently from the same payoff curve for a real strategy shape.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.factory.context_factory import CalculationContextFactory
from app.calculation.providers.dividend_provider import DividendProvider
from app.calculation.providers.expiry_provider import ExpiryProvider
from app.calculation.providers.interest_rate_provider import InterestRateProvider
from app.calculation.providers.market_status_provider import MarketStatusProvider
from app.calculation.providers.time_provider import TimeProvider
from app.calculation.providers.volatility_provider import VolatilityProvider
from app.payoff.engine.payoff_calculator import PayoffCalculator
from app.payoff.models.legs import StrategyLeg
from app.payoff.models.request import PayoffAnalysisRequest
from app.pricing.models.enums import OptionType
from app.probability.models.probability_result import ProbabilityResult

# --- Fixture pattern reused from test_bs_greeks.py / test_active_strategy_pipeline.py ---


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
        return 365 * 24 * 3600  # exactly 1 year, for clean time-value math

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
    """A real CalculationContext with exactly 1 year to expiry, so
    today's Black-Scholes-repriced PnL is genuinely time-valued (not just
    equal to intrinsic value)."""
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


def _request(legs: tuple[StrategyLeg, ...], spot: Decimal, expected_value: Decimal | None) -> PayoffAnalysisRequest:
    return PayoffAnalysisRequest(
        context=_context(spot), pricing_result=None, greeks_result=None, volatility_result=None,
        probability_result=ProbabilityResult(expected_value=expected_value, probability_of_profit=Decimal("0.5")),
        legs=legs,
    )


class TestBullCallSpreadWiring:
    """Buy 100C@5, sell 110C@2 -- net debit 3, max gain 7, max loss -3,
    breakeven at 103 (strike + net debit)."""

    def _legs(self) -> tuple[StrategyLeg, ...]:
        return (
            _leg(OptionType.CALL, 1, Decimal("100"), Decimal("5")),
            _leg(OptionType.CALL, -1, Decimal("110"), Decimal("2")),
        )

    def test_current_pnl_reflects_time_value_unlike_expiry_pnl(self) -> None:
        """current_pnl is now a real Black-Scholes-repriced ("today") value,
        genuinely distinct from the intrinsic-only expiry_pnl -- this is the
        exact behavior the previous current_pnl == expiry_pnl placeholder
        bug is being fixed to replace."""
        result = PayoffCalculator().calculate(_request(self._legs(), Decimal("105"), None))

        assert isinstance(result.current_pnl, Decimal)
        assert isinstance(result.expiry_pnl, Decimal)
        assert result.current_pnl != result.expiry_pnl
        assert len(result.today_curve.points) == len(result.payoff_curve.points)

    def test_max_gain_and_max_loss_match_hand_computed_values(self) -> None:
        result = PayoffCalculator().calculate(_request(self._legs(), Decimal("105"), None))

        assert result.maximum_gain == Decimal("7")
        assert result.maximum_loss == Decimal("-3")

    def test_risk_reward_ratio_matches_gain_over_loss(self) -> None:
        result = PayoffCalculator().calculate(_request(self._legs(), Decimal("105"), None))

        assert result.risk_reward_ratio == Decimal("7") / Decimal("3")

    def test_breakeven_is_near_strike_plus_net_debit(self) -> None:
        result = PayoffCalculator().calculate(_request(self._legs(), Decimal("105"), None))

        assert len(result.breakevens) == 1
        assert abs(result.breakevens[0] - Decimal("103")) < Decimal("1")

    def test_payoff_curve_and_risk_table_have_matching_point_counts(self) -> None:
        result = PayoffCalculator().calculate(_request(self._legs(), Decimal("105"), None))

        assert len(result.payoff_curve.points) == len(result.risk_table.rows)
        # >= DEFAULT_SAMPLES, not ==: both strikes (100, 110) get injected as
        # guaranteed extra sample points when they don't already land on the
        # evenly-spaced grid -- see test_payoff_curve.py::TestStrikeInjection.
        assert len(result.payoff_curve.points) >= 61


class TestFutureValueWiring:
    def test_future_value_uses_probability_expected_value_when_present(self) -> None:
        legs = (_leg(OptionType.CALL, 1, Decimal("100"), Decimal("5")),)
        result = PayoffCalculator().calculate(_request(legs, Decimal("105"), Decimal("42")))

        assert result.future_value == Decimal("42")
        assert result.probability_weighted_pnl == Decimal("42")

    def test_future_value_falls_back_to_current_pnl_floored_at_zero(self) -> None:
        """current_pnl for a losing long call (spot below strike) is
        negative; future_value floors at 0 when there's no probability
        expected value to use instead."""
        legs = (_leg(OptionType.CALL, 1, Decimal("100"), Decimal("5")),)
        result = PayoffCalculator().calculate(_request(legs, Decimal("80"), None))

        assert result.current_pnl < 0
        assert result.future_value == Decimal("0")
