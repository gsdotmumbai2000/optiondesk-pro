"""Predefined stress scenarios."""

from decimal import Decimal

from app.risk.models.enums import StressShockType
from app.risk.models.stress import StressScenario

PRICE_SHOCKS: tuple[Decimal, ...] = (
    Decimal("-20"),
    Decimal("-10"),
    Decimal("-5"),
    Decimal("-2"),
    Decimal("-1"),
    Decimal("1"),
    Decimal("2"),
    Decimal("5"),
    Decimal("10"),
    Decimal("20"),
)


def price_stress_scenarios() -> tuple[StressScenario, ...]:
    """Return underlying price shock scenarios."""
    return tuple(
        StressScenario(
            scenario_id=f"price_{pct}%",
            shock_type=StressShockType.PRICE,
            price_shift_pct=pct,
        )
        for pct in PRICE_SHOCKS
    )


def iv_stress_scenario(iv_shift_pct: Decimal = Decimal("25")) -> StressScenario:
    """Return IV shock scenario."""
    return StressScenario(
        scenario_id=f"iv_{iv_shift_pct}%",
        shock_type=StressShockType.IV,
        iv_shift_pct=iv_shift_pct,
    )


def time_decay_scenario(days: int = 7) -> StressScenario:
    """Return time decay stress scenario."""
    return StressScenario(
        scenario_id=f"time_{days}d",
        shock_type=StressShockType.TIME,
        time_decay_days=days,
    )


def rate_shock_scenario(rate_shift_pct: Decimal = Decimal("1")) -> StressScenario:
    """Return interest rate shock scenario."""
    return StressScenario(
        scenario_id=f"rate_{rate_shift_pct}%",
        shock_type=StressShockType.RATE,
        rate_shift_pct=rate_shift_pct,
    )


def combined_stress_scenario() -> StressScenario:
    """Return combined multi-factor stress scenario."""
    return StressScenario(
        scenario_id="combined_stress",
        shock_type=StressShockType.COMBINED,
        price_shift_pct=Decimal("-10"),
        iv_shift_pct=Decimal("25"),
        time_decay_days=7,
        rate_shift_pct=Decimal("1"),
    )


def all_stress_scenarios() -> tuple[StressScenario, ...]:
    """Return all predefined stress scenarios."""
    return price_stress_scenarios() + (
        iv_stress_scenario(),
        time_decay_scenario(),
        rate_shock_scenario(),
        combined_stress_scenario(),
    )
