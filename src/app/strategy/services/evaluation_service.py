"""Strategy evaluation service."""

from datetime import datetime, timezone

from app.strategy.analytics.aggregator import AnalysisAggregator
from app.strategy.analytics.recommendation import build_recommendation
from app.strategy.engine.strategy_engine import StrategyEngine
from app.strategy.models.evaluation import StrategyEvaluation
from app.strategy.models.request import StrategyEvaluationRequest
from app.strategy.recognition.recognizer import recognize_strategy
from app.strategy.validation.strategy_validator import StrategyValidator


class StrategyEvaluationService:
    """Evaluate strategies via engine orchestration."""

    def __init__(
        self,
        engine: StrategyEngine,
        validator: StrategyValidator | None = None,
        aggregator: AnalysisAggregator | None = None,
    ) -> None:
        """Initialize evaluation service."""
        self._engine = engine
        self._validator = validator or StrategyValidator()
        self._aggregator = aggregator or AnalysisAggregator()

    def evaluate(self, request: StrategyEvaluationRequest) -> StrategyEvaluation:
        """Evaluate strategy by orchestrating frozen engines."""
        self._validator.validate_evaluation_request(request)
        context = self._engine.evaluate_context(request)
        analysis = self._aggregator.aggregate(context)
        recognized = recognize_strategy(request.legs)
        strategy = request.strategy
        if strategy.metadata.recognized_type != recognized:
            from dataclasses import replace

            updated_meta = replace(strategy.metadata, recognized_type=recognized)
            strategy = replace(strategy, metadata=updated_meta)
        recommendation = build_recommendation(analysis)
        return StrategyEvaluation(
            strategy=strategy,
            analysis=analysis,
            recommendation=recommendation,
            evaluated_at=datetime.now(timezone.utc),
        )

    def evaluate_batch(
        self,
        requests: tuple[StrategyEvaluationRequest, ...],
    ) -> tuple[StrategyEvaluation, ...]:
        """Batch evaluate multiple strategies."""
        return tuple(self.evaluate(req) for req in requests)
