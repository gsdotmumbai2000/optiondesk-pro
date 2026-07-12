"""Strategy template service."""

from app.strategy.builders.strategy_builder import StrategyBuilder
from app.strategy.cache.strategy_cache import StrategyCache
from app.strategy.models.strategy import Strategy
from app.strategy.models.template import StrategyTemplate
from app.strategy.serialization.json_serializer import (
    deserialize_strategy,
    serialize_strategy,
    serialize_template,
)
from app.strategy.templates.builtin import get_builtin_templates


class StrategyTemplateService:
    """Manage built-in and custom strategy templates."""

    def __init__(self, cache: StrategyCache | None = None) -> None:
        """Initialize template service."""
        self._cache = cache or StrategyCache()

    def list_builtin(self) -> tuple[StrategyTemplate, ...]:
        """Return built-in templates."""
        return get_builtin_templates()

    def list_custom(self) -> tuple[StrategyTemplate, ...]:
        """Return custom templates from cache."""
        return self._cache.list_templates()

    def save_custom(self, template: StrategyTemplate) -> None:
        """Save custom template."""
        self._cache.put_template(template)

    def from_template(self, template: StrategyTemplate) -> Strategy:
        """Instantiate strategy from template."""
        builder = StrategyBuilder(name=template.name)
        for leg in template.legs:
            builder.add_leg(leg)
        return builder.build()

    def export_template(self, template: StrategyTemplate) -> str:
        """Export template to JSON."""
        return serialize_template(template)

    def export_strategy(self, strategy: Strategy) -> str:
        """Export strategy to JSON."""
        return serialize_strategy(strategy)

    def import_strategy_json(self, data: str) -> dict:
        """Import strategy JSON (returns dict for builder use)."""
        return deserialize_strategy(data)
