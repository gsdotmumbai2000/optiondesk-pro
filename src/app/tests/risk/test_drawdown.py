"""Tests for maximum_drawdown()."""

from datetime import datetime, timezone
from decimal import Decimal

from app.payoff.models.result import (
    PayoffCurve,
    PayoffResult,
    PayoffRiskRow,
    PayoffRiskTable,
)
from app.risk.analytics.drawdown import maximum_drawdown


def _payoff(
    *, risk_rows: tuple[PayoffRiskRow, ...] = (), maximum_loss: Decimal | None = None,
) -> PayoffResult:
    return PayoffResult(
        current_pnl=Decimal("0"), expiry_pnl=Decimal("0"), future_value=Decimal("0"),
        maximum_gain=None, maximum_loss=maximum_loss, risk_reward_ratio=None, breakevens=(),
        payoff_curve=PayoffCurve(), risk_table=PayoffRiskTable(rows=risk_rows),
        probability_weighted_pnl=None, calculation_timestamp=datetime.now(timezone.utc),
    )


def _row(pnl: str) -> PayoffRiskRow:
    return PayoffRiskRow(underlying_price=Decimal("100"), pnl=Decimal(pnl))


class TestWithRiskTableRows:
    def test_returns_absolute_value_of_worst_negative_pnl(self) -> None:
        payoff = _payoff(risk_rows=(_row("-30"), _row("5"), _row("-10")))

        assert maximum_drawdown(payoff) == Decimal("30")

    def test_all_positive_pnl_rows_return_zero(self) -> None:
        payoff = _payoff(risk_rows=(_row("5"), _row("10")))

        assert maximum_drawdown(payoff) == Decimal("0")


class TestEmptyRiskTableFallsBackToMaximumLoss:
    def test_falls_back_to_absolute_maximum_loss(self) -> None:
        payoff = _payoff(risk_rows=(), maximum_loss=Decimal("-45"))

        assert maximum_drawdown(payoff) == Decimal("45")

    def test_no_data_at_all_returns_zero(self) -> None:
        payoff = _payoff(risk_rows=(), maximum_loss=None)

        assert maximum_drawdown(payoff) == Decimal("0")
