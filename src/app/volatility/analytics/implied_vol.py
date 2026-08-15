"""Implied volatility analytics."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.models.snapshots import OptionChainSnapshot, OptionStrikeSnapshot
from app.pricing.black_scholes.solver import implied_volatility as solve_bs_iv
from app.pricing.models.enums import OptionType

_FALLBACK_VOLATILITY = Decimal("0.20")


def _solve_from_traded_price(
    strike: OptionStrikeSnapshot,
    context: CalculationContext,
) -> Decimal | None:
    """Solve IV from the strike's traded price when no quoted IV is available."""
    spot = float(context.spot_price)
    rate = float(context.risk_free_rate)
    dividend_yield = float(context.dividend_yield)
    time_to_expiry = float(context.time_to_expiry)
    strike_price = float(strike.strike_price)

    if strike.call_ltp is not None and strike.call_ltp > 0:
        solved = solve_bs_iv(
            float(strike.call_ltp), spot, strike_price, rate, dividend_yield,
            time_to_expiry, OptionType.CALL,
        )
        if solved is not None:
            return Decimal(str(solved))
    if strike.put_ltp is not None and strike.put_ltp > 0:
        solved = solve_bs_iv(
            float(strike.put_ltp), spot, strike_price, rate, dividend_yield,
            time_to_expiry, OptionType.PUT,
        )
        if solved is not None:
            return Decimal(str(solved))
    return None


def resolve_implied_volatility(
    context: CalculationContext,
    option_chain: OptionChainSnapshot,
) -> Decimal:
    """Resolve implied volatility from context, chain-quoted IV, or by
    solving it from the chain's traded option price (Black-Scholes
    inversion) when no quote is available. Falls back to a flat 20% only
    when the chain has no usable IV or price data at all."""
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
            solved = _solve_from_traded_price(strike, context)
            if solved is not None:
                return solved
    for strike in option_chain.strikes:
        if strike.call_iv is not None and strike.call_iv > 0:
            return strike.call_iv
        if strike.put_iv is not None and strike.put_iv > 0:
            return strike.put_iv
    for strike in option_chain.strikes:
        solved = _solve_from_traded_price(strike, context)
        if solved is not None:
            return solved
    return _FALLBACK_VOLATILITY
