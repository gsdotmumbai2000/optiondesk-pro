"""Explanation application service."""

from app.ai.explainability.evidence_builder import EvidenceBuilder
from app.ai.explainability.explainer import ExplanationBuilder
from app.ai.models.context import EngineContextSnapshot
from app.ai.models.explanation import Explanation
from app.ai.models.evidence import SupportingEvidence
from app.ai.models.request import RecommendationAnalysisRequest
from app.ai.models.rules import RecommendationRule


class ExplanationService:
    """Expose explainability builders."""

    def __init__(self) -> None:
        """Initialize explainability components."""
        self._evidence = EvidenceBuilder()
        self._explainer = ExplanationBuilder()

    def build_evidence(
        self,
        request: RecommendationAnalysisRequest,
        context: EngineContextSnapshot,
        rule: RecommendationRule,
    ) -> SupportingEvidence:
        """Build supporting evidence."""
        return self._evidence.build(request, context, rule)

    def build_explanation(
        self,
        rule: RecommendationRule,
        context: EngineContextSnapshot,
        evidence: SupportingEvidence,
    ) -> Explanation:
        """Build detailed explanation."""
        return self._explainer.build(rule, context, evidence)
