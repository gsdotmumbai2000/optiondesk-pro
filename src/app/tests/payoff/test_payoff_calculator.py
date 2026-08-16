"""Engine-level wiring tests for PayoffCalculator: proves current_pnl,
expiry_pnl, max_gain/loss, breakevens, and future_value are all derived
consistently from the same payoff curve for a real strategy shape.
"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.payoff.engine.payoff_calculator import PayoffCalculator
from app.payoff.models.legs import StrategyLeg
from app.payoff.models.request import PayoffAnalysisRequest
from app.pricing.models.enums import OptionType
from app.probability.models.probability_result import ProbabilityResult


def _context(spot: Decimal) -> SimpleNamespace:
    return SimpleNamespace(spot_price=spot, tick_size=Decimal("0.05"))


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

    def test_current_pnl_and_expiry_pnl_match_at_expiry_valuation(self) -> None:
        result = PayoffCalculator().calculate(_request(self._legs(), Decimal("105"), None))

        assert result.current_pnl == result.expiry_pnl

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
        assert len(result.payoff_curve.points) == 21  # DEFAULT_SAMPLES


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
