"""Tests for expected_value(): theoretical_price + a liquidity-weighted
expected-move adjustment. Deterministic arithmetic -- verified by hand.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.option_chain.models.analysis import OptionChainAnalysis
from app.pricing.models.pricing_result import PricingResult
from app.probability.analytics.expected_value import expected_value
from app.volatility.models.volatility_result import (
    ExpectedMove,
    HistoricalVolatility,
    VolatilityResult,
)


def _pricing(theoretical_price: Decimal) -> PricingResult:
    return PricingResult(
        theoretical_price=theoretical_price, intrinsic_value=Decimal("0"), extrinsic_value=Decimal("0"),
        d1=Decimal("0"), d2=Decimal("0"), forward_price=Decimal("0"), discount_factor=Decimal("1"),
        calculation_time=datetime.now(timezone.utc),
    )


def _volatility(move_to_expiry: Decimal) -> VolatilityResult:
    return VolatilityResult(
        implied_volatility=Decimal("0.2"), annualized_volatility=Decimal("0.2"),
        realized_volatility=Decimal("0.2"), historical_volatility=HistoricalVolatility(primary=Decimal("0.2")),
        expected_move=ExpectedMove(to_expiry=move_to_expiry), iv_percentile=Decimal("50"),
        calculation_timestamp=datetime.now(timezone.utc),
    )


def _chain_analysis(liquidity_score: Decimal) -> OptionChainAnalysis:
    return OptionChainAnalysis(
        liquidity_score=liquidity_score, put_call_ratio=Decimal("1"), atm_iv=Decimal("0.2"),
        total_call_oi=0, total_put_oi=0, skew=None, calculation_timestamp=datetime.now(timezone.utc),
    )


class TestExactArithmetic:
    def test_matches_hand_computed_formula(self) -> None:
        """base=100, move=50, liquidity=80 -> 100 + 50*(80/100)*0.1 = 100 + 4 = 104."""
        result = expected_value(
            _pricing(Decimal("100")), _volatility(Decimal("50")), _chain_analysis(Decimal("80")),
        )

        assert result == Decimal("104")

    def test_matches_hand_computed_formula_second_case(self) -> None:
        """base=250.5, move=20, liquidity=60 -> 250.5 + 20*0.6*0.1 = 250.5 + 1.2 = 251.7."""
        result = expected_value(
            _pricing(Decimal("250.5")), _volatility(Decimal("20")), _chain_analysis(Decimal("60")),
        )

        assert result == Decimal("251.7")


class TestEdgeCases:
    def test_zero_liquidity_returns_exactly_theoretical_price(self) -> None:
        result = expected_value(
            _pricing(Decimal("100")), _volatility(Decimal("50")), _chain_analysis(Decimal("0")),
        )

        assert result == Decimal("100")

    def test_zero_expected_move_returns_exactly_theoretical_price(self) -> None:
        result = expected_value(
            _pricing(Decimal("100")), _volatility(Decimal("0")), _chain_analysis(Decimal("80")),
        )

        assert result == Decimal("100")

    def test_adjustment_scales_linearly_with_liquidity_score(self) -> None:
        low = expected_value(_pricing(Decimal("100")), _volatility(Decimal("50")), _chain_analysis(Decimal("20")))
        high = expected_value(_pricing(Decimal("100")), _volatility(Decimal("50")), _chain_analysis(Decimal("40")))

        assert (high - Decimal("100")) == (low - Decimal("100")) * 2

    def test_adjustment_scales_linearly_with_expected_move(self) -> None:
        small_move = expected_value(_pricing(Decimal("100")), _volatility(Decimal("10")), _chain_analysis(Decimal("50")))
        big_move = expected_value(_pricing(Decimal("100")), _volatility(Decimal("30")), _chain_analysis(Decimal("50")))

        assert (big_move - Decimal("100")) == (small_move - Decimal("100")) * 3
