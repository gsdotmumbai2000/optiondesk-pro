"""Tests for ProbabilityCalculator: combines POP + expected value + a
touch-probability heuristic (pop + 0.15, clamped to 1.0)."""

import math
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.option_chain.models.analysis import OptionChainAnalysis
from app.pricing.models.pricing_result import PricingResult
from app.probability.engine.probability_calculator import ProbabilityCalculator
from app.probability.models.request import ProbabilityAnalysisRequest
from app.volatility.models.volatility_result import (
    ExpectedMove,
    HistoricalVolatility,
    VolatilityResult,
)


def _pricing(d2: Decimal, theoretical_price: Decimal = Decimal("100")) -> PricingResult:
    return PricingResult(
        theoretical_price=theoretical_price, intrinsic_value=Decimal("0"), extrinsic_value=Decimal("0"),
        d1=Decimal("0"), d2=d2, forward_price=Decimal("0"), discount_factor=Decimal("1"),
        calculation_time=datetime.now(timezone.utc),
    )


def _volatility() -> VolatilityResult:
    return VolatilityResult(
        implied_volatility=Decimal("0.2"), annualized_volatility=Decimal("0.2"),
        realized_volatility=Decimal("0.2"), historical_volatility=HistoricalVolatility(primary=Decimal("0.2")),
        expected_move=ExpectedMove(to_expiry=Decimal("0")), iv_percentile=Decimal("50"),
        calculation_timestamp=datetime.now(timezone.utc),
    )


def _chain_analysis() -> OptionChainAnalysis:
    return OptionChainAnalysis(
        liquidity_score=Decimal("0"), put_call_ratio=Decimal("1"), atm_iv=Decimal("0.2"),
        total_call_oi=0, total_put_oi=0, skew=None, calculation_timestamp=datetime.now(timezone.utc),
    )


def _request(d2: Decimal) -> ProbabilityAnalysisRequest:
    return ProbabilityAnalysisRequest(
        context=None, pricing_result=_pricing(d2), greeks_result=None,
        volatility_result=_volatility(), chain_analysis=_chain_analysis(),
    )


class TestProbabilityOfProfitWiring:
    def test_pop_matches_normal_cdf_of_d2(self) -> None:
        result = ProbabilityCalculator().calculate(_request(Decimal("0.5")))

        expected = 0.5 * (1.0 + math.erf(0.5 / math.sqrt(2.0)))
        assert float(result.probability_of_profit) == pytest.approx(expected, abs=1e-9)


class TestTouchProbabilityClamping:
    def test_touch_is_pop_plus_15_points_when_under_one(self) -> None:
        """pop at d2=0 is exactly 0.5, so touch should be 0.65, well under 1."""
        result = ProbabilityCalculator().calculate(_request(Decimal("0")))

        assert result.probability_of_touch == result.probability_of_profit + Decimal("0.15")
        assert result.probability_of_touch < Decimal("1")

    def test_touch_clamps_at_one_when_pop_plus_15_would_exceed_one(self) -> None:
        """pop at a strongly positive d2 approaches 1, so pop + 0.15 must clamp."""
        result = ProbabilityCalculator().calculate(_request(Decimal("5")))

        assert result.probability_of_touch == Decimal("1")

    def test_touch_never_exceeds_one_across_a_range_of_d2(self) -> None:
        for d2 in (Decimal("-3"), Decimal("-1"), Decimal("0"), Decimal("1"), Decimal("3"), Decimal("10")):
            result = ProbabilityCalculator().calculate(_request(d2))
            assert result.probability_of_touch <= Decimal("1")


class TestExpectedValueWiring:
    def test_expected_value_equals_theoretical_price_when_no_move_or_liquidity(self) -> None:
        result = ProbabilityCalculator().calculate(_request(Decimal("0")))

        assert result.expected_value == Decimal("100")
