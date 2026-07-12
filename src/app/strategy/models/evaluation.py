"""Strategy evaluation result."""

from dataclasses import dataclass
from datetime import datetime

from app.strategy.models.analysis import StrategyAnalysis
from app.strategy.models.enums import StrategyModelVersion
from app.strategy.models.score import StrategyRecommendation
from app.strategy.models.strategy import Strategy


@dataclass(frozen=True, slots=True)
class StrategyEvaluation:
    """Complete strategy evaluation output."""

    strategy: Strategy
    analysis: StrategyAnalysis
    recommendation: StrategyRecommendation
    evaluated_at: datetime
    model_version: StrategyModelVersion = StrategyModelVersion.V1
