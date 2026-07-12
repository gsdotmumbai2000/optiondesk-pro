"""Strategy engine entry point."""

from app.strategy.engine.bundle import EngineBundle
from app.strategy.engine.orchestrator import EngineOrchestrator
from app.strategy.models.context import StrategyContext
from app.strategy.models.request import StrategyEvaluationRequest


class StrategyEngine:
    """Enterprise strategy engine."""

    def __init__(self, engines: EngineBundle) -> None:
        """Initialize with injected engine bundle."""
        self._orchestrator = EngineOrchestrator(engines)

    @property
    def orchestrator(self) -> EngineOrchestrator:
        """Return engine orchestrator."""
        return self._orchestrator

    def evaluate_context(
        self, request: StrategyEvaluationRequest
    ) -> StrategyContext:
        """Orchestrate engines and return strategy context."""
        return self._orchestrator.orchestrate(request)
