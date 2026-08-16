"""Tests for the three VaR methods (historical, parametric, variance-
covariance) and expected shortfall (CVaR). Every expected value is hand-
computed from the same formula the code uses (z_score lookup x volatility
x portfolio value), so a wrong z-score, wrong daily-vol conversion, or
swapped operand would be caught.
"""

from datetime import datetime, timezone
from decimal import Decimal

from app.risk.analytics.expected_shortfall import expected_shortfall
from app.risk.analytics.var_historical import historical_var
from app.risk.analytics.var_parametric import parametric_var
from app.risk.analytics.var_variance_covariance import variance_covariance_var
from app.risk.models.enums import ConfidenceLevel, VaRMethod
from app.volatility.models.volatility_result import (
    ExpectedMove,
    HistoricalVolatility,
    VolatilityResult,
)

_P95_Z = Decimal("1.645")
_P99_Z = Decimal("2.326")


def _volatility(*, historical: Decimal | None, realized: Decimal = Decimal("0.2")) -> VolatilityResult:
    return VolatilityResult(
        implied_volatility=Decimal("0.2"), annualized_volatility=Decimal("0.2"),
        realized_volatility=realized, historical_volatility=HistoricalVolatility(primary=historical),
        expected_move=ExpectedMove(to_expiry=Decimal("0")), iv_percentile=Decimal("50"),
        calculation_timestamp=datetime.now(timezone.utc),
    )


class TestParametricVar:
    def test_matches_hand_computed_value_at_p95(self) -> None:
        """portfolio=100,000, vol=0.02 (2% daily) -> VaR = 100000*0.02*1.645 = 3290."""
        result = parametric_var(Decimal("100000"), Decimal("0.02"), ConfidenceLevel.P95)

        assert result.value_at_risk == Decimal("100000") * Decimal("0.02") * _P95_Z
        assert result.method == VaRMethod.PARAMETRIC
        assert result.confidence == ConfidenceLevel.P95
        assert result.portfolio_value == Decimal("100000")

    def test_p99_var_exceeds_p95_var_for_same_inputs(self) -> None:
        p95 = parametric_var(Decimal("100000"), Decimal("0.02"), ConfidenceLevel.P95)
        p99 = parametric_var(Decimal("100000"), Decimal("0.02"), ConfidenceLevel.P99)

        assert p99.value_at_risk > p95.value_at_risk

    def test_var_scales_linearly_with_portfolio_value(self) -> None:
        small = parametric_var(Decimal("10000"), Decimal("0.02"), ConfidenceLevel.P95)
        large = parametric_var(Decimal("20000"), Decimal("0.02"), ConfidenceLevel.P95)

        assert large.value_at_risk == small.value_at_risk * 2


class TestVarianceCovarianceVar:
    def test_matches_hand_computed_value_converting_annual_to_daily_vol(self) -> None:
        """portfolio=100,000, annual vol=0.3 -> daily = 0.3/15.8745,
        VaR = 100000 * (0.3/15.8745) * 1.645."""
        result = variance_covariance_var(Decimal("100000"), Decimal("0.3"), ConfidenceLevel.P95)

        daily_vol = Decimal("0.3") / Decimal("15.8745")
        assert result.value_at_risk == Decimal("100000") * daily_vol * _P95_Z
        assert result.method == VaRMethod.VARIANCE_COVARIANCE

    def test_annualized_conversion_reduces_var_versus_treating_vol_as_daily(self) -> None:
        """Using the annual->daily conversion must produce a materially
        smaller VaR than (incorrectly) treating the annual vol as daily --
        catches an accidental removal of the /15.8745 conversion."""
        converted = variance_covariance_var(Decimal("100000"), Decimal("0.3"), ConfidenceLevel.P95)
        naive = parametric_var(Decimal("100000"), Decimal("0.3"), ConfidenceLevel.P95)

        assert converted.value_at_risk < naive.value_at_risk


class TestHistoricalVar:
    def test_uses_volatility_result_historical_primary_when_present(self) -> None:
        volatility = _volatility(historical=Decimal("0.25"))
        context = _fake_context(historical_volatility=None)

        result = historical_var(Decimal("100000"), context, volatility, ConfidenceLevel.P95)

        daily_vol = Decimal("0.25") / Decimal("15.8745")
        assert result.value_at_risk == Decimal("100000") * daily_vol * _P95_Z
        assert result.method == VaRMethod.HISTORICAL

    def test_falls_back_to_context_historical_volatility_when_result_has_none(self) -> None:
        volatility = _volatility(historical=None)
        context = _fake_context(historical_volatility=Decimal("0.28"))

        result = historical_var(Decimal("100000"), context, volatility, ConfidenceLevel.P95)

        daily_vol = Decimal("0.28") / Decimal("15.8745")
        assert result.value_at_risk == Decimal("100000") * daily_vol * _P95_Z

    def test_falls_back_to_realized_volatility_as_last_resort(self) -> None:
        volatility = _volatility(historical=None, realized=Decimal("0.22"))
        context = _fake_context(historical_volatility=None)

        result = historical_var(Decimal("100000"), context, volatility, ConfidenceLevel.P95)

        daily_vol = Decimal("0.22") / Decimal("15.8745")
        assert result.value_at_risk == Decimal("100000") * daily_vol * _P95_Z

    def test_zero_historical_volatility_falls_through_to_next_source(self) -> None:
        """historical_volatility.primary=0 is falsy-invalid (<=0 guard), not
        a real zero-vol reading -- must fall through, not produce VaR=0."""
        volatility = _volatility(historical=Decimal("0"), realized=Decimal("0.22"))
        context = _fake_context(historical_volatility=None)

        result = historical_var(Decimal("100000"), context, volatility, ConfidenceLevel.P95)

        assert result.value_at_risk > Decimal("0")


class TestExpectedShortfall:
    def test_es_exceeds_var_for_positive_volatility(self) -> None:
        """Tail loss (ES - VaR) must be positive whenever volatility > 0 --
        expected shortfall is always at least as severe as VaR."""
        var_result = parametric_var(Decimal("100000"), Decimal("0.02"), ConfidenceLevel.P95)

        es = expected_shortfall(var_result.value_at_risk, Decimal("0.02"), ConfidenceLevel.P95)

        assert es.expected_shortfall > var_result.value_at_risk
        assert es.tail_loss > Decimal("0")

    def test_matches_hand_computed_tail_factor_formula(self) -> None:
        """VaR=3290, vol=0.02, z=1.645 -> tail_factor = 1 + 0.02/(1.645*2),
        ES = 3290 * tail_factor."""
        var = Decimal("3290")
        result = expected_shortfall(var, Decimal("0.02"), ConfidenceLevel.P95)

        tail_factor = Decimal("1") + Decimal("0.02") / (_P95_Z * Decimal("2"))
        assert result.expected_shortfall == var * tail_factor
        assert result.tail_loss == var * tail_factor - var

    def test_zero_volatility_means_es_equals_var(self) -> None:
        result = expected_shortfall(Decimal("3290"), Decimal("0"), ConfidenceLevel.P95)

        assert result.expected_shortfall == Decimal("3290")
        assert result.tail_loss == Decimal("0")


def _fake_context(*, historical_volatility: Decimal | None):
    from types import SimpleNamespace

    return SimpleNamespace(historical_volatility=historical_volatility)
