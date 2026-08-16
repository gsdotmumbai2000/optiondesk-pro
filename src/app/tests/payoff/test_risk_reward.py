"""Tests for risk_reward_ratio()."""

from decimal import Decimal

from app.payoff.analytics.risk_reward import risk_reward_ratio


class TestNormalCase:
    def test_ratio_equals_gain_over_absolute_loss(self) -> None:
        assert risk_reward_ratio(Decimal("100"), Decimal("-50")) == Decimal("2")

    def test_ratio_below_one_when_loss_exceeds_gain(self) -> None:
        assert risk_reward_ratio(Decimal("25"), Decimal("-100")) == Decimal("0.25")


class TestNoneInputs:
    def test_none_gain_returns_none(self) -> None:
        assert risk_reward_ratio(None, Decimal("-50")) is None

    def test_none_loss_returns_none(self) -> None:
        assert risk_reward_ratio(Decimal("50"), None) is None

    def test_both_none_returns_none(self) -> None:
        assert risk_reward_ratio(None, None) is None


class TestInvalidLoss:
    def test_non_negative_loss_returns_none(self) -> None:
        """A "maximum loss" that isn't actually negative is invalid input --
        the ratio is undefined, not zero or infinite."""
        assert risk_reward_ratio(Decimal("100"), Decimal("0")) is None
        assert risk_reward_ratio(Decimal("100"), Decimal("50")) is None


class TestNonPositiveGain:
    def test_zero_or_negative_gain_returns_zero(self) -> None:
        assert risk_reward_ratio(Decimal("0"), Decimal("-50")) == Decimal("0")
        assert risk_reward_ratio(Decimal("-10"), Decimal("-50")) == Decimal("0")
