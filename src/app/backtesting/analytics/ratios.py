"""Risk-adjusted ratio calculations."""

import math
from decimal import Decimal


def sharpe_ratio(returns: tuple[Decimal, ...], risk_free: Decimal = Decimal("0")) -> Decimal:
    """Compute Sharpe ratio from return series."""
    if not returns:
        return Decimal("0")
    mean = sum(returns) / Decimal(len(returns))
    excess = mean - risk_free
    variance = sum((r - mean) ** 2 for r in returns) / Decimal(len(returns))
    std = Decimal(str(math.sqrt(float(variance)))) if variance > 0 else Decimal("0.0001")
    return excess / std


def sortino_ratio(returns: tuple[Decimal, ...], risk_free: Decimal = Decimal("0")) -> Decimal:
    """Compute Sortino ratio from return series."""
    if not returns:
        return Decimal("0")
    mean = sum(returns) / Decimal(len(returns))
    excess = mean - risk_free
    downside = [min(r - risk_free, Decimal("0")) for r in returns]
    down_var = sum(d ** 2 for d in downside) / Decimal(len(returns))
    down_std = (
        Decimal(str(math.sqrt(float(down_var)))) if down_var > 0 else Decimal("0.0001")
    )
    return excess / down_std


def calmar_ratio(returns: tuple[Decimal, ...], max_drawdown: Decimal) -> Decimal:
    """Compute Calmar ratio."""
    if not returns or max_drawdown <= 0:
        return Decimal("0")
    annual_return = sum(returns) / Decimal(len(returns)) * Decimal("252")
    return annual_return / max_drawdown
