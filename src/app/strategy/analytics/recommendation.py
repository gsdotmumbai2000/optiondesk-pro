"""Strategy recommendation builder."""

from decimal import Decimal

from app.strategy.models.analysis import StrategyAnalysis
from app.strategy.models.score import StrategyRecommendation


def build_recommendation(analysis: StrategyAnalysis) -> StrategyRecommendation:
    """Build recommendation from analysis scores."""
    score = analysis.score.overall_score
    strategy_id = analysis.context.legs[0].leg_id if analysis.context.legs else ""
    if score >= Decimal("70"):
        rec, conf = "FAVORABLE", Decimal("0.8")
    elif score >= Decimal("40"):
        rec, conf = "NEUTRAL", Decimal("0.5")
    else:
        rec, conf = "UNFAVORABLE", Decimal("0.3")
    rationale = (
        f"Overall score {score:.1f}; POP {analysis.probability_of_profit:.2%}"
    )
    return StrategyRecommendation(
        strategy_id=strategy_id,
        recommendation=rec,
        confidence=conf,
        rationale=rationale,
    )
