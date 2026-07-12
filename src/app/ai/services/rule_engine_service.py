"""Rule engine application service."""

from app.ai.models.rules import RecommendationRule
from app.ai.rules.rule_registry import RuleRegistry
from app.ai.validation.recommendation_validator import RecommendationValidator


class RuleEngineService:
    """Manage configurable recommendation rules."""

    def __init__(
        self,
        registry: RuleRegistry | None = None,
        validator: RecommendationValidator | None = None,
    ) -> None:
        """Initialize rule engine service."""
        self._registry = registry or RuleRegistry()
        self._validator = validator or RecommendationValidator()

    def rules(self) -> tuple[RecommendationRule, ...]:
        """Return all rules."""
        return self._registry.all_rules()

    def register(self, rule: RecommendationRule) -> None:
        """Register custom rule."""
        self._validator.validate_rule(rule)
        self._registry.register(rule)

    def enabled_rules(
        self,
        overrides: tuple[RecommendationRule, ...] = (),
    ) -> tuple[RecommendationRule, ...]:
        """Return enabled rules."""
        return self._registry.enabled_rules(overrides)
