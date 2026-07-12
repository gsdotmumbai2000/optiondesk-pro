"""Margin reduction suggestions."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.margin.analytics.margin_benefit import margin_benefit
from app.margin.models.optimization import MarginReductionSuggestion
from app.payoff.models.legs import StrategyLeg


def generate_suggestions(
    legs: tuple[StrategyLeg, ...],
    context: CalculationContext,
    current_margin: Decimal,
) -> tuple[MarginReductionSuggestion, ...]:
    """Generate margin reduction suggestions."""
    suggestions: list[MarginReductionSuggestion] = []
    benefit = margin_benefit(legs, context)
    if benefit > 0:
        suggestions.append(
            MarginReductionSuggestion(
                suggestion_id="hedge_offset",
                description="Increase offsetting legs to capture margin benefit",
                estimated_reduction=benefit * Decimal("0.5"),
                priority=1,
            )
        )
    short_legs = [leg for leg in legs if leg.quantity < 0]
    if len(short_legs) > 2:
        suggestions.append(
            MarginReductionSuggestion(
                suggestion_id="reduce_shorts",
                description="Reduce naked short legs to lower SPAN margin",
                estimated_reduction=current_margin * Decimal("0.15"),
                priority=2,
            )
        )
    return tuple(suggestions)
