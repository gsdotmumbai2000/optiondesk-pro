"""Greeks summary adapter from risk engine."""

from decimal import Decimal

from app.portfolio.models.result import GreeksSummary
from app.risk.models.result import RiskResult


class GreeksAdapter:
    """Map risk engine output to portfolio greeks summary."""

    def from_risk(self, risk: RiskResult | None) -> GreeksSummary:
        """Build greeks summary without local calculation."""
        if risk is None:
            zero = Decimal("0")
            return GreeksSummary(
                net_delta=zero,
                net_gamma=zero,
                net_theta=zero,
                net_vega=zero,
            )
        return GreeksSummary(
            net_delta=risk.net_delta,
            net_gamma=risk.net_gamma,
            net_theta=risk.net_theta,
            net_vega=risk.net_vega,
        )
