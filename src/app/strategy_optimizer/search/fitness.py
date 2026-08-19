"""Real per-candidate fitness scoring for search algorithms that need
feedback to guide their search (e.g. Simulated Annealing) -- unlike
BruteForceSearch/HeuristicSearch, which just slice the given candidate
list, since OptimizerEngine.optimize() runs search() *before* evaluation.

Wraps the same evaluator + objective-weighting path the rest of the
optimizer pipeline uses (ObjectiveWeighter, previously wired but never
called), so a search algorithm's notion of "better" matches what the user
actually asked to optimize for (OptimizationPreferences.primary_objective),
not an arbitrary proxy metric invented at the search layer.
"""

from decimal import Decimal

from app.strategy.exceptions import InvalidStrategyInput
from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.engine.ports import EvaluationPort
from app.strategy_optimizer.engine.request_builder import build_evaluation_request
from app.strategy_optimizer.models.request import OptimizationRequest
from app.strategy_optimizer.objectives.weighter import ObjectiveWeighter


class CandidateFitnessEvaluator:
    """Score a single candidate strategy via a real engine evaluation."""

    def __init__(self, evaluator: EvaluationPort, request: OptimizationRequest) -> None:
        self._evaluator = evaluator
        self._request = request
        self._weighter = ObjectiveWeighter()

    def score(self, strategy: Strategy) -> Decimal | None:
        """Return the objective-weighted fitness for `strategy`, or None
        when it fails validation (e.g. a degenerate leg combination) --
        callers should treat that candidate as unusable, not crash the
        search over a single bad candidate."""
        eval_request = build_evaluation_request(strategy, self._request)
        try:
            evaluation = self._evaluator.evaluate(eval_request)
        except InvalidStrategyInput:
            return None
        return self._weighter.weight(evaluation, self._request.preferences)
