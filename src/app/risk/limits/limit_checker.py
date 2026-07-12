"""Risk limit checker."""

from decimal import Decimal

from app.risk.models.limits import RiskLimitConfig, RiskLimitWarning


def check_limits(
    config: RiskLimitConfig,
    *,
    net_delta: Decimal,
    net_gamma: Decimal,
    net_vega: Decimal,
    current_pnl: Decimal,
    margin_utilization: Decimal,
    position_size: int,
    capital_exposure: Decimal,
) -> tuple[RiskLimitWarning, ...]:
    """Check risk metrics against configured limits."""
    warnings: list[RiskLimitWarning] = []
    checks = [
        ("max_delta", config.max_delta, abs(net_delta)),
        ("max_gamma", config.max_gamma, abs(net_gamma)),
        ("max_vega", config.max_vega, abs(net_vega)),
        ("max_loss", config.max_loss, abs(min(current_pnl, Decimal("0")))),
        ("max_margin", config.max_margin, margin_utilization),
        ("max_position_size", config.max_position_size, Decimal(position_size)),
        ("max_capital_exposure", config.max_capital_exposure, capital_exposure),
    ]
    for name, limit, actual in checks:
        if limit is None:
            continue
        limit_dec = Decimal(limit) if not isinstance(limit, Decimal) else limit
        if actual > limit_dec:
            warnings.append(
                RiskLimitWarning(
                    limit_name=name,
                    limit_value=limit_dec,
                    actual_value=actual,
                    message=f"{name} exceeded: {actual} > {limit_dec}",
                )
            )
    return tuple(warnings)
