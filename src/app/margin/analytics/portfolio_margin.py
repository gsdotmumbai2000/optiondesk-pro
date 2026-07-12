"""Portfolio margin aggregation."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.margin.analytics.leg_margin import leg_initial_margin, leg_notional
from app.margin.analytics.margin_benefit import margin_benefit
from app.payoff.models.legs import StrategyLeg
from app.risk.models.result import RiskResult


def portfolio_margin_totals(
    legs: tuple[StrategyLeg, ...],
    context: CalculationContext,
    risk: RiskResult,
) -> dict[str, Decimal]:
    """Compute portfolio margin components."""
    initial = Decimal("0")
    span = Decimal("0")
    exposure = Decimal("0")
    for leg in legs:
        leg_init, leg_span, leg_exp = leg_initial_margin(leg, context)
        initial += leg_init
        span += leg_span
        exposure += leg_exp
    benefit = margin_benefit(legs, context)
    portfolio = initial - benefit
    additional = risk.capital_at_risk * Decimal("0.1")
    total = portfolio + additional
    return {
        "initial": initial,
        "span": span,
        "exposure": exposure,
        "portfolio": portfolio,
        "additional": additional,
        "total": total,
        "benefit": benefit,
    }


def total_notional(
    legs: tuple[StrategyLeg, ...],
    context: CalculationContext,
) -> Decimal:
    """Return aggregate notional across legs."""
    return sum(leg_notional(leg, context) for leg in legs)
