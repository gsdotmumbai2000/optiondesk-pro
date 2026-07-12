"""Evaluation port for dependency injection."""

from typing import Protocol

from app.strategy.models.evaluation import StrategyEvaluation
from app.strategy.models.request import StrategyEvaluationRequest


class EvaluationPort(Protocol):
    """Strategy evaluation port."""

    def evaluate(self, request: StrategyEvaluationRequest) -> StrategyEvaluation:
        """Evaluate a single strategy."""
        ...

    def evaluate_batch(
        self,
        requests: tuple[StrategyEvaluationRequest, ...],
    ) -> tuple[StrategyEvaluation, ...]:
        """Batch evaluate strategies."""
        ...
