"""Tests for check_limits(): each configured threshold independently, plus
the None-limit-means-unchecked and multi-breach cases.
"""

from decimal import Decimal

from app.risk.limits.limit_checker import check_limits
from app.risk.models.limits import RiskLimitConfig


def _check(config: RiskLimitConfig, **overrides):
    defaults = dict(
        net_delta=Decimal("0"), net_gamma=Decimal("0"), net_vega=Decimal("0"),
        current_pnl=Decimal("0"), margin_utilization=Decimal("0"), position_size=0,
        capital_exposure=Decimal("0"),
    )
    defaults.update(overrides)
    return check_limits(config, **defaults)


class TestNoLimitsConfiguredMeansNoWarnings:
    def test_all_none_config_produces_no_warnings_regardless_of_values(self) -> None:
        warnings = _check(
            RiskLimitConfig(), net_delta=Decimal("999999"), current_pnl=Decimal("-999999"),
        )

        assert warnings == ()


class TestEachLimitTypeIndependently:
    def test_delta_breach_produces_warning(self) -> None:
        warnings = _check(RiskLimitConfig(max_delta=Decimal("100")), net_delta=Decimal("150"))

        assert len(warnings) == 1
        assert warnings[0].limit_name == "max_delta"
        assert warnings[0].actual_value == Decimal("150")
        assert warnings[0].limit_value == Decimal("100")

    def test_delta_uses_absolute_value_so_large_negative_delta_also_breaches(self) -> None:
        warnings = _check(RiskLimitConfig(max_delta=Decimal("100")), net_delta=Decimal("-150"))

        assert len(warnings) == 1
        assert warnings[0].actual_value == Decimal("150")

    def test_gamma_breach_produces_warning(self) -> None:
        warnings = _check(RiskLimitConfig(max_gamma=Decimal("10")), net_gamma=Decimal("15"))

        assert len(warnings) == 1
        assert warnings[0].limit_name == "max_gamma"

    def test_vega_breach_produces_warning(self) -> None:
        warnings = _check(RiskLimitConfig(max_vega=Decimal("500")), net_vega=Decimal("600"))

        assert len(warnings) == 1
        assert warnings[0].limit_name == "max_vega"

    def test_max_loss_only_counts_negative_pnl(self) -> None:
        """Profitable positions (positive current_pnl) never breach max_loss
        -- only losses (clamped at 0 on the profit side) count."""
        warnings = _check(RiskLimitConfig(max_loss=Decimal("1000")), current_pnl=Decimal("5000"))

        assert warnings == ()

    def test_max_loss_breach_on_actual_loss(self) -> None:
        warnings = _check(RiskLimitConfig(max_loss=Decimal("1000")), current_pnl=Decimal("-1500"))

        assert len(warnings) == 1
        assert warnings[0].limit_name == "max_loss"
        assert warnings[0].actual_value == Decimal("1500")

    def test_margin_utilization_breach(self) -> None:
        warnings = _check(RiskLimitConfig(max_margin=Decimal("0.8")), margin_utilization=Decimal("0.95"))

        assert len(warnings) == 1
        assert warnings[0].limit_name == "max_margin"

    def test_position_size_breach(self) -> None:
        warnings = _check(RiskLimitConfig(max_position_size=10), position_size=15)

        assert len(warnings) == 1
        assert warnings[0].limit_name == "max_position_size"

    def test_capital_exposure_breach(self) -> None:
        warnings = _check(
            RiskLimitConfig(max_capital_exposure=Decimal("50000")), capital_exposure=Decimal("60000"),
        )

        assert len(warnings) == 1
        assert warnings[0].limit_name == "max_capital_exposure"


class TestAtLimitDoesNotBreach:
    def test_exactly_at_limit_is_not_a_breach(self) -> None:
        """Only strictly-greater-than triggers a warning."""
        warnings = _check(RiskLimitConfig(max_delta=Decimal("100")), net_delta=Decimal("100"))

        assert warnings == ()


class TestMultipleSimultaneousBreaches:
    def test_multiple_breached_limits_all_reported(self) -> None:
        config = RiskLimitConfig(max_delta=Decimal("100"), max_gamma=Decimal("10"), max_vega=Decimal("500"))
        warnings = _check(config, net_delta=Decimal("150"), net_gamma=Decimal("20"), net_vega=Decimal("100"))

        names = {w.limit_name for w in warnings}
        assert names == {"max_delta", "max_gamma"}
