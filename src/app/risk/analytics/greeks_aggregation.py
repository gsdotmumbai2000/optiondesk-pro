"""Portfolio Greeks aggregation."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.greeks.models.greeks_result import GreeksResult
from app.payoff.models.legs import StrategyLeg
from app.pricing.models.enums import OptionType


def _leg_scale(leg: StrategyLeg) -> Decimal:
    return Decimal(leg.quantity) * Decimal(leg.multiplier)


def _matches_context(leg: StrategyLeg, context: CalculationContext) -> bool:
    return leg.strike == context.atm_strike and leg.expiry == context.expiry


def _type_sign(leg: StrategyLeg) -> Decimal:
    return Decimal("1") if leg.option_type == OptionType.CALL else Decimal("-1")


def aggregate_greeks(
    legs: tuple[StrategyLeg, ...],
    context: CalculationContext,
    greeks: GreeksResult,
) -> dict[str, Decimal]:
    """Aggregate net portfolio Greeks from reference greeks and legs."""
    totals = {
        "delta": Decimal("0"),
        "gamma": Decimal("0"),
        "theta": Decimal("0"),
        "vega": Decimal("0"),
        "rho": Decimal("0"),
        "vanna": Decimal("0"),
        "charm": Decimal("0"),
        "vomma": Decimal("0"),
    }
    for leg in legs:
        scale = _leg_scale(leg)
        if _matches_context(leg, context):
            totals["delta"] += greeks.delta * scale
            totals["gamma"] += greeks.gamma * scale
            totals["theta"] += greeks.theta * scale
            totals["vega"] += greeks.vega * scale
            totals["rho"] += greeks.rho * scale
            totals["vanna"] += greeks.vanna * scale
            totals["charm"] += greeks.charm * scale
            totals["vomma"] += greeks.vomma * scale
        else:
            strike_shift = leg.strike - context.atm_strike
            sign = _type_sign(leg)
            totals["delta"] += (greeks.delta + greeks.gamma * strike_shift * sign) * scale
            totals["gamma"] += greeks.gamma * scale
            totals["theta"] += greeks.theta * scale
            totals["vega"] += greeks.vega * scale
            totals["rho"] += greeks.rho * scale
            totals["vanna"] += greeks.vanna * scale
            totals["charm"] += greeks.charm * scale
            totals["vomma"] += greeks.vomma * scale
    return totals
