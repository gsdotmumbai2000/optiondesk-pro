"""Evaluation service adapter."""

from app.strategy.services.evaluation_service import StrategyEvaluationService
from app.strategy_optimizer.engine.ports import EvaluationPort


class EvaluationServiceAdapter:
    """Adapter wrapping StrategyEvaluationService."""

    def __init__(self, service: StrategyEvaluationService) -> None:
        """Initialize adapter."""
        self._service = service

    def evaluate(self, request):
        return self._service.evaluate(request)

    def evaluate_batch(self, requests):
        return self._service.evaluate_batch(requests)
