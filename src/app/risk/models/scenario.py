"""Risk scenario models."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class RiskScenario:
    """Single risk scenario definition."""

    scenario_id: str
    price_shift_pct: Decimal = Decimal("0")
    iv_shift_pct: Decimal = Decimal("0")
    time_decay_days: int = 0
    rate_shift_pct: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class RiskScenarioResult:
    """Result of a single risk scenario."""

    scenario_id: str
    scenario_loss: Decimal
    pnl_change: Decimal
    rank: int = 0


@dataclass(frozen=True, slots=True)
class ScenarioComparison:
    """Comparison of multiple scenario results."""

    scenarios: tuple[RiskScenarioResult, ...]
    worst_case_id: str
    best_case_id: str


@dataclass(frozen=True, slots=True)
class ScenarioRanking:
    """Ranked scenario results."""

    ranked: tuple[RiskScenarioResult, ...]
