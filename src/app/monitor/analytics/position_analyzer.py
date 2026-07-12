"""Position snapshot and health analytics."""

from datetime import datetime, timezone
from decimal import Decimal

from app.monitor.models.alert import Alert
from app.monitor.models.enums import AlertPriority, PositionHealth
from app.monitor.models.monitor import PositionSnapshot
from app.portfolio.models.positions import Position


class PositionAnalyzer:
    """Build position snapshots and aggregate health."""

    def snapshots(
        self,
        positions: tuple[Position, ...],
        alerts: tuple[Alert, ...],
    ) -> tuple[PositionSnapshot, ...]:
        """Create position snapshots from portfolio positions."""
        alert_symbols = {a.symbol for a in alerts if a.symbol}
        now = datetime.now(timezone.utc)
        result: list[PositionSnapshot] = []
        for pos in positions:
            health = self._position_health(pos, alert_symbols, alerts)
            result.append(
                PositionSnapshot(
                    position_id=pos.position_id,
                    symbol=pos.symbol,
                    quantity=pos.quantity,
                    unrealized_pnl=pos.unrealized_pnl,
                    health=health,
                    captured_at=now,
                )
            )
        return tuple(result)

    def aggregate_health(
        self,
        alerts: tuple[Alert, ...],
        snapshots: tuple[PositionSnapshot, ...],
    ) -> PositionHealth:
        """Derive portfolio position status from alerts."""
        if any(a.priority == AlertPriority.EMERGENCY for a in alerts):
            return PositionHealth.CRITICAL
        if any(a.priority == AlertPriority.CRITICAL for a in alerts):
            return PositionHealth.CRITICAL
        if any(a.priority == AlertPriority.WARNING for a in alerts):
            return PositionHealth.AT_RISK
        if snapshots and any(s.health == PositionHealth.WATCH for s in snapshots):
            return PositionHealth.WATCH
        return PositionHealth.HEALTHY

    def _position_health(
        self,
        position: Position,
        alert_symbols: set[str],
        alerts: tuple[Alert, ...],
    ) -> PositionHealth:
        if position.symbol in alert_symbols:
            sym_alerts = [a for a in alerts if a.symbol == position.symbol]
            if any(a.priority == AlertPriority.CRITICAL for a in sym_alerts):
                return PositionHealth.CRITICAL
            return PositionHealth.AT_RISK
        if position.unrealized_pnl < Decimal("0"):
            return PositionHealth.WATCH
        return PositionHealth.HEALTHY
