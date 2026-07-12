"""AI rules package."""

from app.ai.rules.builtin_rules import default_rules
from app.ai.rules.rule_engine import RecommendationRuleEngine
from app.ai.rules.rule_registry import RuleRegistry

__all__ = ["RecommendationRuleEngine", "RuleRegistry", "default_rules"]
