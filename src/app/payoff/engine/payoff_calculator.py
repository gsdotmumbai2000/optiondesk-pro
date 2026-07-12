"""Payoff calculator."""

from datetime import datetime, timezone
from decimal import Decimal

from app.payoff.analytics.breakevens import find_breakevens
from app.payoff.analytics.expiry_payoff import total_expiry_pnl
from app.payoff.analytics.payoff_curve import build_payoff_curve
from app.payoff.analytics.risk_reward import risk_reward_ratio as calc_risk_reward
from app.payoff.analytics.risk_table import build_risk_table, curve_extrema
from app.payoff.models.enums import PayoffModelVersion
from app.payoff.models.request import PayoffAnalysisRequest
from app.payoff.models.result import PayoffResult


class PayoffCalculator:
    """Calculate full payoff analytics from request bundle."""

    def calculate(self, request: PayoffAnalysisRequest) -> PayoffResult:
        """Compute PayoffResult from request."""
        legs = request.resolved_legs
        ctx = request.context
        spot = ctx.spot_price
        probability = request.probability_result

        current_pnl = total_expiry_pnl(spot, legs)
        expiry_pnl = current_pnl
        curve = build_payoff_curve(legs, ctx)
        max_gain, max_loss = curve_extrema(curve)
        breakevens = find_breakevens(curve)
        risk_table = build_risk_table(curve)
        rr_ratio = calc_risk_reward(max_gain, max_loss)

        probability_weighted = probability.expected_value
        if probability_weighted is not None:
            future_value = probability_weighted
        else:
            future_value = max(current_pnl, Decimal("0"))

        return PayoffResult(
            current_pnl=current_pnl,
            expiry_pnl=expiry_pnl,
            future_value=future_value,
            maximum_gain=max_gain,
            maximum_loss=max_loss,
            risk_reward_ratio=rr_ratio,
            breakevens=breakevens,
            payoff_curve=curve,
            risk_table=risk_table,
            probability_weighted_pnl=probability_weighted,
            calculation_timestamp=datetime.now(timezone.utc),
            model_version=PayoffModelVersion.V1,
        )
