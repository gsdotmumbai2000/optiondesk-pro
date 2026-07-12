"""Portfolio health score calculator."""

from decimal import Decimal

from app.monitor.models.alert import Alert
from app.monitor.models.enums import AlertPriority, PositionHealth


class HealthScorer:
    """Compute health score from alerts and position status."""

    def score(
        self,
        alerts: tuple[Alert, ...],
        position_status: PositionHealth,
    ) -> Decimal:
        """Return health score 0-100 (higher is healthier)."""
        base = {
            PositionHealth.HEALTHY: Decimal("100"),
            PositionHealth.WATCH: Decimal("75"),
            PositionHealth.AT_RISK: Decimal("50"),
            PositionHealth.CRITICAL: Decimal("25"),
        }.get(position_status, Decimal("50"))
        penalty = Decimal("0")
        for alert in alerts:
            penalty += self._penalty(alert.priority)
        return max(base - penalty, Decimal("0"))

    def _penalty(self, priority: AlertPriority) -> Decimal:
        return {
            AlertPriority.INFORMATION: Decimal("2"),
            AlertPriority.WARNING: Decimal("10"),
            AlertPriority.CRITICAL: Decimal("20"),
            AlertPriority.EMERGENCY: Decimal("30"),
        }.get(priority, Decimal("5"))
