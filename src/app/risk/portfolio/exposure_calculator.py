"""Portfolio exposure calculator."""

from collections import defaultdict
from decimal import Decimal

from app.payoff.models.legs import StrategyLeg
from app.risk.models.exposure import (
    ExpiryExposure,
    OptionTypeExposure,
    PortfolioExposure,
    SectorExposure,
    UnderlyingExposure,
)


def _leg_notional(leg: StrategyLeg) -> Decimal:
    return abs(Decimal(leg.quantity) * Decimal(leg.multiplier) * leg.strike)


def calculate_exposure(legs: tuple[StrategyLeg, ...]) -> PortfolioExposure:
    """Compute portfolio exposure breakdown."""
    if not legs:
        return PortfolioExposure(
            total_notional=Decimal("0"),
            underlying=(),
            expiry=(),
            option_type=(),
            sector=(),
        )
    underlying_map: dict[str, Decimal] = defaultdict(Decimal)
    expiry_map: dict[str, Decimal] = defaultdict(Decimal)
    type_map: dict[str, Decimal] = defaultdict(Decimal)
    total = Decimal("0")
    for leg in legs:
        n = _leg_notional(leg)
        total += n
        key = leg.underlying or "default"
        underlying_map[key] += n
        expiry_map[str(leg.expiry)] += n
        type_map[leg.option_type.value] += n

    def _weights(data: dict[str, Decimal]) -> Decimal:
        return total if total > 0 else Decimal("1")

    uw = _weights(underlying_map)
    return PortfolioExposure(
        total_notional=total,
        underlying=tuple(
            UnderlyingExposure(u, v, v / uw) for u, v in sorted(underlying_map.items())
        ),
        expiry=tuple(
            ExpiryExposure(e, v, v / uw) for e, v in sorted(expiry_map.items())
        ),
        option_type=tuple(
            OptionTypeExposure(t, v, v / uw) for t, v in sorted(type_map.items())
        ),
        sector=tuple(
            SectorExposure(u, v, v / uw) for u, v in sorted(underlying_map.items())
        ),
    )
