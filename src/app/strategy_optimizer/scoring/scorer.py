"""Optimizer scoring from engine outputs."""

from decimal import Decimal

from app.strategy.models.evaluation import StrategyEvaluation
from app.strategy_optimizer.models.candidate import GreeksSummary
from app.strategy_optimizer.models.scoring import OptimizerScore


def score_evaluation(evaluation: StrategyEvaluation) -> OptimizerScore:
    """Map engine outputs to optimizer scores (no local math)."""
    ctx = evaluation.analysis.context
    engine_score = evaluation.analysis.score
    margin = ctx.margin_result
    prob = ctx.probability_result
    vol = ctx.volatility_result

    return OptimizerScore(
        risk_score=engine_score.risk_score,
        reward_score=engine_score.reward_score,
        pop_score=prob.probability_of_profit * Decimal("100"),
        liquidity_score=evaluation.analysis.liquidity_score,
        margin_score=Decimal("100") - margin.margin_utilization * Decimal("100"),
        theta_score=abs(ctx.risk_result.net_theta),
        volatility_score=Decimal("100") - vol.iv_percentile,
        capital_efficiency=margin.capital_efficiency,
        overall_score=engine_score.overall_score,
    )


def greeks_summary(evaluation: StrategyEvaluation) -> GreeksSummary:
    """Extract greeks summary from risk engine output."""
    risk = evaluation.analysis.context.risk_result
    return GreeksSummary(
        net_delta=risk.net_delta,
        net_gamma=risk.net_gamma,
        net_theta=risk.net_theta,
        net_vega=risk.net_vega,
    )
