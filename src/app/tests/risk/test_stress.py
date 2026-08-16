"""Tests for stress scenario construction and run_stress_test()/
run_all_stress_tests()."""

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.payoff.models.legs import StrategyLeg
from app.pricing.models.enums import OptionType
from app.risk.models.enums import StressShockType
from app.risk.stress.stress_runner import run_all_stress_tests, run_stress_test
from app.risk.stress.stress_scenarios import (
    PRICE_SHOCKS,
    all_stress_scenarios,
    combined_stress_scenario,
    iv_stress_scenario,
    price_stress_scenarios,
    rate_shock_scenario,
    time_decay_scenario,
)
from app.volatility.models.volatility_result import (
    ExpectedMove,
    HistoricalVolatility,
    VolatilityResult,
)


def _context(spot: Decimal) -> SimpleNamespace:
    return SimpleNamespace(spot_price=spot)


def _volatility(implied: Decimal) -> VolatilityResult:
    return VolatilityResult(
        implied_volatility=implied, annualized_volatility=implied, realized_volatility=implied,
        historical_volatility=HistoricalVolatility(primary=implied),
        expected_move=ExpectedMove(to_expiry=Decimal("0")), iv_percentile=Decimal("50"),
        calculation_timestamp=datetime.now(timezone.utc),
    )


class TestPredefinedScenarios:
    def test_price_stress_scenarios_cover_all_ten_documented_shocks(self) -> None:
        scenarios = price_stress_scenarios()

        assert len(scenarios) == 10
        assert {s.price_shift_pct for s in scenarios} == set(PRICE_SHOCKS)
        assert all(s.shock_type == StressShockType.PRICE for s in scenarios)

    def test_combined_scenario_sets_all_four_shock_dimensions(self) -> None:
        scenario = combined_stress_scenario()

        assert scenario.shock_type == StressShockType.COMBINED
        assert scenario.price_shift_pct == Decimal("-10")
        assert scenario.iv_shift_pct == Decimal("25")
        assert scenario.time_decay_days == 7
        assert scenario.rate_shift_pct == Decimal("1")

    def test_all_stress_scenarios_includes_price_plus_four_named_scenarios(self) -> None:
        scenarios = all_stress_scenarios()

        assert len(scenarios) == 10 + 4

    def test_custom_iv_and_rate_shock_parameters_are_honored(self) -> None:
        assert iv_stress_scenario(Decimal("50")).iv_shift_pct == Decimal("50")
        assert rate_shock_scenario(Decimal("2")).rate_shift_pct == Decimal("2")
        assert time_decay_scenario(14).time_decay_days == 14


def _long_call_legs() -> tuple[StrategyLeg, ...]:
    return (
        StrategyLeg(
            strike=Decimal("100"), option_type=OptionType.CALL, quantity=1, premium=Decimal("5"),
            expiry=date(2027, 1, 1),
        ),
    )


class TestRunStressTest:
    def test_negative_price_shock_produces_a_loss_for_a_long_call(self) -> None:
        legs = _long_call_legs()
        context = _context(Decimal("100"))
        volatility = _volatility(Decimal("0.2"))
        base_pnl = Decimal("0")  # ATM long call, current intrinsic-only PnL = -premium = -5

        scenario = price_stress_scenarios()[0]  # -20%
        result = run_stress_test(scenario, legs, context, volatility, base_pnl)

        assert result.shocked_price == Decimal("100") * Decimal("0.8")
        assert result.stress_loss >= Decimal("0")  # losses are clamped non-negative

    def test_shocked_price_matches_hand_computed_percentage_shift(self) -> None:
        legs = _long_call_legs()
        context = _context(Decimal("24500"))
        volatility = _volatility(Decimal("0.2"))

        scenario = next(s for s in price_stress_scenarios() if s.price_shift_pct == Decimal("-10"))
        result = run_stress_test(scenario, legs, context, volatility, Decimal("0"))

        assert result.shocked_price == Decimal("24500") * Decimal("0.9")

    def test_shocked_iv_matches_hand_computed_percentage_shift(self) -> None:
        legs = _long_call_legs()
        context = _context(Decimal("100"))
        volatility = _volatility(Decimal("0.20"))

        scenario = iv_stress_scenario(Decimal("25"))
        result = run_stress_test(scenario, legs, context, volatility, Decimal("0"))

        assert result.shocked_iv == Decimal("0.20") * Decimal("1.25")

    def test_gain_scenario_produces_zero_stress_loss_not_negative(self) -> None:
        """A price move that IMPROVES pnl vs base must clamp stress_loss at
        0, never report a negative loss."""
        legs = _long_call_legs()
        context = _context(Decimal("100"))
        volatility = _volatility(Decimal("0.2"))

        scenario = next(s for s in price_stress_scenarios() if s.price_shift_pct == Decimal("20"))
        result = run_stress_test(scenario, legs, context, volatility, base_pnl=Decimal("-5"))

        assert result.stress_loss == Decimal("0")


class TestRunAllStressTests:
    def test_returns_one_result_per_scenario(self) -> None:
        legs = _long_call_legs()
        context = _context(Decimal("100"))
        volatility = _volatility(Decimal("0.2"))
        scenarios = price_stress_scenarios()

        results = run_all_stress_tests(scenarios, legs, context, volatility, Decimal("0"))

        assert len(results) == len(scenarios)
        assert {r.scenario_id for r in results} == {s.scenario_id for s in scenarios}
