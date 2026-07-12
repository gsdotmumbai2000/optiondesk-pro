"""Recommendation rule registry."""

from app.ai.models.rules import RecommendationRule
from app.ai.rules.builtin_rules import default_rules


class RuleRegistry:
    """Manage built-in and custom recommendation rules."""

    def __init__(self) -> None:
        """Initialize registry."""
        self._custom: list[RecommendationRule] = []

    def all_rules(self) -> tuple[RecommendationRule, ...]:
        """Return all rules."""
        return default_rules() + tuple(self._custom)

    def register(self, rule: RecommendationRule) -> None:
        """Register custom rule."""
        self._custom.append(rule)

    def enabled_rules(
        self,
        overrides: tuple[RecommendationRule, ...] = (),
    ) -> tuple[RecommendationRule, ...]:
        """Return enabled rules."""
        base = overrides if overrides else self.all_rules()
        return tuple(r for r in base if r.enabled)
