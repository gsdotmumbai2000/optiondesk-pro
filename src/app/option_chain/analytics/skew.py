"""Volatility skew analytics."""

from decimal import Decimal

from app.calculation.models.snapshots import OptionChainSnapshot
from app.volatility.models.volatility_result import VolatilityResult


def atm_iv(
    option_chain: OptionChainSnapshot,
    volatility: VolatilityResult,
) -> Decimal:
    """Resolve ATM implied volatility from chain or volatility result."""
    for strike in option_chain.strikes:
        if strike.is_atm:
            if strike.call_iv is not None and strike.call_iv > 0:
                return strike.call_iv
            if strike.put_iv is not None and strike.put_iv > 0:
                return strike.put_iv
    return volatility.implied_volatility


def skew(option_chain: OptionChainSnapshot, atm: Decimal) -> Decimal | None:
    """Estimate put/call IV skew."""
    otm_puts = [s.put_iv for s in option_chain.strikes if s.put_iv and s.put_iv > 0]
    otm_calls = [s.call_iv for s in option_chain.strikes if s.call_iv and s.call_iv > 0]
    if not otm_puts or not otm_calls or atm <= 0:
        return None
    return max(otm_puts) - min(otm_calls)
