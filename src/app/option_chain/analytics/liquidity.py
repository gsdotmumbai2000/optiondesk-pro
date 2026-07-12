"""Option chain liquidity analytics."""

from decimal import Decimal

from app.calculation.models.snapshots import OptionChainSnapshot


def liquidity_score(option_chain: OptionChainSnapshot) -> Decimal:
    """Estimate chain liquidity from open interest."""
    if not option_chain.strikes:
        return Decimal("50")
    total_oi = sum(
        (strike.call_oi or 0) + (strike.put_oi or 0)
        for strike in option_chain.strikes
    )
    if total_oi <= 0:
        return Decimal("40")
    if total_oi >= 1_000_000:
        return Decimal("90")
    if total_oi >= 100_000:
        return Decimal("75")
    return Decimal("60")
