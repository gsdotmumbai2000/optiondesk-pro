"""Strategy scoring from engine outputs (orchestration only)."""

from decimal import Decimal

from app.strategy.models.context import StrategyContext
from app.strategy.models.score import StrategyScore


def compute_scores(context: StrategyContext) -> StrategyScore:
    """Map engine results to strategy scores."""
    risk = context.risk_result
    margin = context.margin_result
    prob = context.probability_result
    vol = context.volatility_result

    risk_score = _clamp(risk.risk_score)
    reward_score = _reward_from_payoff(context)
    cap_eff = _clamp(margin.capital_efficiency * Decimal("10"))
    liquidity = _liquidity_from_chain(context)
    prob_score = _clamp(prob.probability_of_profit * Decimal("100"))
    vol_score = _clamp(Decimal("100") - vol.iv_percentile)

    overall = (
        reward_score * Decimal("0.25")
        + prob_score * Decimal("0.25")
        + cap_eff * Decimal("0.20")
        - risk_score * Decimal("0.15")
        + liquidity * Decimal("0.10")
        + vol_score * Decimal("0.05")
    )
    return StrategyScore(
        risk_score=risk_score,
        reward_score=reward_score,
        capital_efficiency=cap_eff,
        liquidity_score=liquidity,
        probability_score=prob_score,
        volatility_score=vol_score,
        overall_score=_clamp(overall),
    )


def _reward_from_payoff(context: StrategyContext) -> Decimal:
    payoff = context.payoff_result
    if payoff.maximum_profit is None:
        return Decimal("50")
    return _clamp(abs(payoff.maximum_profit) / Decimal("100"))


def _liquidity_from_chain(context: StrategyContext) -> Decimal:
    return Decimal("70")


def _clamp(value: Decimal) -> Decimal:
    return min(max(value, Decimal("0")), Decimal("100"))
