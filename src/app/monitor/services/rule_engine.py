"""Rule engine service."""

from app.monitor.models.alert import AlertRule
from app.monitor.rules.rule_registry import RuleRegistry
from app.monitor.validation.monitor_validator import MonitorValidator


class RuleEngine:
    """Manage and validate alert rules."""

    def __init__(
        self,
        registry: RuleRegistry | None = None,
        validator: MonitorValidator | None = None,
    ) -> None:
        """Initialize rule engine."""
        self._registry = registry or RuleRegistry()
        self._validator = validator or MonitorValidator()

    def rules(self) -> tuple[AlertRule, ...]:
        """Return all rules."""
        return self._registry.all_rules()

    def enabled_rules(
        self,
        overrides: tuple[AlertRule, ...] = (),
    ) -> tuple[AlertRule, ...]:
        """Return enabled rules."""
        return self._registry.enabled_rules(overrides)

    def register(self, rule: AlertRule) -> None:
        """Register custom rule."""
        self._validator.validate_rule(rule)
        self._registry.register(rule)
