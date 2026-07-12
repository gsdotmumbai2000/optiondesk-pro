"""Built-in alert rule definitions."""

from decimal import Decimal

from app.monitor.models.alert import AlertRule
from app.monitor.models.enums import AlertPriority, RuleType
from app.utils.uuid_helper import generate_uuid


def default_rules() -> tuple[AlertRule, ...]:
    """Return default monitoring rules."""
    return (
        _rule(RuleType.MAX_LOSS, "Maximum Loss", Decimal("-5000"), AlertPriority.CRITICAL),
        _rule(RuleType.MAX_PROFIT, "Maximum Profit", Decimal("10000"), AlertPriority.INFORMATION),
        _rule(RuleType.MAX_DELTA, "Maximum Delta", Decimal("100"), AlertPriority.WARNING),
        _rule(RuleType.MAX_GAMMA, "Maximum Gamma", Decimal("50"), AlertPriority.WARNING),
        _rule(RuleType.MAX_VEGA, "Maximum Vega", Decimal("5000"), AlertPriority.WARNING),
        _rule(RuleType.MAX_THETA, "Maximum Theta", Decimal("-500"), AlertPriority.WARNING),
        _rule(RuleType.MAX_MARGIN, "Maximum Margin", Decimal("0.80"), AlertPriority.CRITICAL),
        _rule(RuleType.MAX_DRAWDOWN, "Maximum Drawdown", Decimal("0.15"), AlertPriority.CRITICAL),
        _rule(RuleType.TIME_TO_EXPIRY, "Time To Expiry", Decimal("3"), AlertPriority.WARNING),
        _rule(RuleType.IV_SPIKE, "IV Spike", Decimal("0.05"), AlertPriority.WARNING),
        _rule(RuleType.IV_CRUSH, "IV Crush", Decimal("-0.05"), AlertPriority.INFORMATION),
        _rule(RuleType.OI_SHIFT, "OI Shift", Decimal("0.20"), AlertPriority.INFORMATION),
        _rule(RuleType.PRICE_GAP, "Price Gap", Decimal("0.03"), AlertPriority.WARNING),
    )


def _rule(
    rule_type: RuleType,
    name: str,
    threshold: Decimal,
    priority: AlertPriority,
) -> AlertRule:
    return AlertRule(
        rule_id=generate_uuid(),
        rule_type=rule_type,
        name=name,
        threshold=threshold,
        priority=priority,
    )
