"""Alert rule registry with custom rule support."""

from app.monitor.models.alert import AlertRule
from app.monitor.rules.builtin_rules import default_rules


class RuleRegistry:
    """Manage built-in and custom alert rules."""

    def __init__(self) -> None:
        """Initialize registry."""
        self._custom: list[AlertRule] = []

    def all_rules(self) -> tuple[AlertRule, ...]:
        """Return built-in plus custom rules."""
        return default_rules() + tuple(self._custom)

    def register(self, rule: AlertRule) -> None:
        """Register a custom rule."""
        self._custom.append(rule)

    def enabled_rules(
        self,
        overrides: tuple[AlertRule, ...] = (),
    ) -> tuple[AlertRule, ...]:
        """Return enabled rules, preferring overrides when provided."""
        base = overrides if overrides else self.all_rules()
        return tuple(r for r in base if r.enabled)
