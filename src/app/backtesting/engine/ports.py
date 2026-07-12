"""Evaluation port for backtesting."""

from typing import Protocol

from app.strategy.models.evaluation import StrategyEvaluation
from app.strategy.models.request import StrategyEvaluationRequest


class EvaluationPort(Protocol):
    """Strategy evaluation port."""

    def evaluate(self, request: StrategyEvaluationRequest) -> StrategyEvaluation:
        """Evaluate strategy at a point in time."""
        ...
