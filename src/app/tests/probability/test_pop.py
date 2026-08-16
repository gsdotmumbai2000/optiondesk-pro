"""Tests for probability_of_profit(): risk-neutral N(d2)/N(-d2)."""

import math
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.pricing.models.enums import OptionType
from app.pricing.models.option_contract import OptionContract
from app.pricing.models.pricing_result import PricingResult
from app.probability.analytics.pop import probability_of_profit


def _reference_cdf(x: float) -> float:
    """Independent normal CDF via math.erf -- not app.pricing.black_scholes."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _pricing(d2: Decimal) -> PricingResult:
    return PricingResult(
        theoretical_price=Decimal("0"), intrinsic_value=Decimal("0"), extrinsic_value=Decimal("0"),
        d1=Decimal("0"), d2=d2, forward_price=Decimal("0"), discount_factor=Decimal("1"),
        calculation_time=datetime.now(timezone.utc),
    )


def _contract(option_type: OptionType) -> OptionContract:
    from datetime import date

    return OptionContract(strike=Decimal("100"), option_type=option_type, expiry=date(2027, 1, 1))


class TestMatchesReferenceNormalCdf:
    @pytest.mark.parametrize("d2", [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0])
    def test_call_pop_equals_cdf_of_d2(self, d2: float) -> None:
        pop = probability_of_profit(_pricing(Decimal(str(d2))), _contract(OptionType.CALL))

        assert float(pop) == pytest.approx(_reference_cdf(d2), abs=1e-9)

    @pytest.mark.parametrize("d2", [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0])
    def test_put_pop_equals_cdf_of_negative_d2(self, d2: float) -> None:
        pop = probability_of_profit(_pricing(Decimal(str(d2))), _contract(OptionType.PUT))

        assert float(pop) == pytest.approx(_reference_cdf(-d2), abs=1e-9)

    def test_no_contract_defaults_to_call_behavior(self) -> None:
        pop = probability_of_profit(_pricing(Decimal("0.5")))

        assert float(pop) == pytest.approx(_reference_cdf(0.5), abs=1e-9)


class TestInvariants:
    """Hold for any d2 -- no reference numbers needed."""

    @pytest.mark.parametrize("d2", [-3.0, -1.0, 0.0, 1.0, 3.0])
    def test_call_and_put_pop_sum_to_one(self, d2: float) -> None:
        call_pop = probability_of_profit(_pricing(Decimal(str(d2))), _contract(OptionType.CALL))
        put_pop = probability_of_profit(_pricing(Decimal(str(d2))), _contract(OptionType.PUT))

        assert float(call_pop + put_pop) == pytest.approx(1.0, abs=1e-9)

    @pytest.mark.parametrize("d2", [-5.0, -1.0, 0.0, 1.0, 5.0])
    def test_call_pop_always_in_zero_one_bounds(self, d2: float) -> None:
        pop = probability_of_profit(_pricing(Decimal(str(d2))), _contract(OptionType.CALL))

        assert Decimal("0") <= pop <= Decimal("1")

    def test_call_pop_at_d2_zero_is_one_half(self) -> None:
        """N(0) = 0.5 exactly -- ATM-equivalent d2, a genuine known constant."""
        pop = probability_of_profit(_pricing(Decimal("0")), _contract(OptionType.CALL))

        assert float(pop) == pytest.approx(0.5, abs=1e-9)

    def test_call_pop_increases_monotonically_with_d2(self) -> None:
        d2_values = [-2.0, -1.0, 0.0, 1.0, 2.0]
        pops = [
            probability_of_profit(_pricing(Decimal(str(d2))), _contract(OptionType.CALL))
            for d2 in d2_values
        ]

        assert pops == sorted(pops)

    def test_deeply_negative_d2_call_pop_approaches_zero(self) -> None:
        pop = probability_of_profit(_pricing(Decimal("-10")), _contract(OptionType.CALL))

        assert float(pop) < 1e-6

    def test_deeply_positive_d2_call_pop_approaches_one(self) -> None:
        pop = probability_of_profit(_pricing(Decimal("10")), _contract(OptionType.CALL))

        assert float(pop) > 1.0 - 1e-6
