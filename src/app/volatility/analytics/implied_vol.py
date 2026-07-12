"""Implied volatility analytics."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.models.snapshots import OptionChainSnapshot


def resolve_implied_volatility(
    context: CalculationContext,
    option_chain: OptionChainSnapshot,
) -> Decimal:
    """Resolve implied volatility from context or chain ATM IV."""
    if context.implied_volatility is not None and context.implied_volatility > 0:
        return context.implied_volatility
    if context.volatility > 0:
        return context.volatility
    for strike in option_chain.strikes:
        if strike.is_atm:
            if strike.call_iv is not None and strike.call_iv > 0:
                return strike.call_iv
            if strike.put_iv is not None and strike.put_iv > 0:
                return strike.put_iv
    for strike in option_chain.strikes:
        if strike.call_iv is not None and strike.call_iv > 0:
            return strike.call_iv
        if strike.put_iv is not None and strike.put_iv > 0:
            return strike.put_iv
    return Decimal("0.20")
