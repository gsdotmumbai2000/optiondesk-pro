"""Strategy analysis aggregator (no calculations)."""

from decimal import Decimal

from app.strategy.models.analysis import StrategyAnalysis
from app.strategy.models.context import StrategyContext
from app.strategy.models.enums import StrategyType
from app.strategy.models.score import StrategyScore
from app.strategy.recognition.recognizer import recognize_strategy
from app.strategy.analytics.scoring import compute_scores


class AnalysisAggregator:
    """Aggregate engine results into strategy analysis."""

    def aggregate(self, context: StrategyContext) -> StrategyAnalysis:
        """Build strategy analysis from context."""
        recognized = recognize_strategy(context.legs)
        scores = compute_scores(context)
        vol = context.volatility_result
        margin = context.margin_result
        prob = context.probability_result
        return StrategyAnalysis(
            context=context,
            recognized_type=recognized,
            probability_of_profit=prob.probability_of_profit,
            expected_move=vol.expected_move.to_expiry,
            capital_efficiency=margin.capital_efficiency,
            margin_utilization=margin.margin_utilization,
            liquidity_score=scores.liquidity_score,
            strategy_rating=scores.overall_score,
            score=scores,
        )
