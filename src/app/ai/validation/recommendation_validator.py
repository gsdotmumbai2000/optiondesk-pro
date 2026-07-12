"""AI recommendation validation."""

from decimal import Decimal

from app.ai.exceptions import InvalidRecommendationInput, MissingEvidenceError
from app.ai.models.evidence import SupportingEvidence
from app.ai.models.request import RecommendationAnalysisRequest
from app.ai.models.result import RecommendationResult
from app.ai.models.rules import RecommendationRule


class RecommendationValidator:
    """Validate AI inputs and recommendation outputs."""

    def validate_request(self, request: RecommendationAnalysisRequest) -> None:
        """Validate analysis request."""
        if not request.session_id:
            raise InvalidRecommendationInput("session_id is required")
        if request.portfolio_result.portfolio_value < 0:
            raise InvalidRecommendationInput("portfolio_value cannot be negative")

    def validate_rule(self, rule: RecommendationRule) -> None:
        """Validate recommendation rule."""
        if not rule.rule_id:
            raise InvalidRecommendationInput("rule_id is required")
        if not rule.suggested_action:
            raise InvalidRecommendationInput("suggested_action is required")

    def validate_evidence(self, evidence: SupportingEvidence) -> None:
        """Validate supporting evidence."""
        if not evidence.metrics:
            raise MissingEvidenceError("recommendation must include evidence metrics")
        for metric in evidence.metrics:
            if not metric.engine_reference:
                raise InvalidRecommendationInput("metric must reference engine source")

    def validate_result(self, result: RecommendationResult) -> None:
        """Validate recommendation result."""
        self.validate_evidence(result.supporting_evidence)
        if not result.detailed_explanation.why:
            raise MissingEvidenceError("recommendation must include explanation")
        if result.confidence_score < Decimal("0") or result.confidence_score > Decimal("1"):
            raise InvalidRecommendationInput("confidence_score must be between 0 and 1")
