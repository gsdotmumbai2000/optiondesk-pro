"""Risk summary adapter from risk engine."""

from decimal import Decimal

from app.portfolio.models.result import RiskSummary
from app.risk.models.result import RiskResult


class RiskAdapter:
    """Map risk engine output to portfolio risk summary."""

    def from_risk(self, risk: RiskResult | None) -> RiskSummary:
        """Build risk summary without local calculation."""
        if risk is None:
            zero = Decimal("0")
            return RiskSummary(
                value_at_risk=zero,
                risk_score=zero,
                capital_at_risk=zero,
            )
        return RiskSummary(
            value_at_risk=risk.value_at_risk,
            risk_score=risk.risk_score,
            capital_at_risk=risk.capital_at_risk,
        )
