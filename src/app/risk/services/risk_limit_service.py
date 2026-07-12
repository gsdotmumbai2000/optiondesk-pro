"""Risk limit application service."""

from decimal import Decimal

from app.risk.limits.limit_checker import check_limits
from app.risk.models.limits import RiskLimitConfig, RiskLimitWarning


class RiskLimitService:
    """Service for risk limit checking."""

    def check(
        self,
        config: RiskLimitConfig,
        *,
        net_delta: Decimal,
        net_gamma: Decimal,
        net_vega: Decimal,
        current_pnl: Decimal,
        margin_utilization: Decimal,
        position_size: int,
        capital_exposure: Decimal,
    ) -> tuple[RiskLimitWarning, ...]:
        """Check limits and return warnings."""
        return check_limits(
            config,
            net_delta=net_delta,
            net_gamma=net_gamma,
            net_vega=net_vega,
            current_pnl=current_pnl,
            margin_utilization=margin_utilization,
            position_size=position_size,
            capital_exposure=capital_exposure,
        )

    def has_violations(self, warnings: tuple[RiskLimitWarning, ...]) -> bool:
        """Return True if any limit warnings exist."""
        return len(warnings) > 0
