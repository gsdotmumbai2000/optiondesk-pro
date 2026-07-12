"""Stress test models."""

from dataclasses import dataclass
from decimal import Decimal

from app.risk.models.enums import StressShockType


@dataclass(frozen=True, slots=True)
class StressScenario:
    """Predefined or custom stress scenario."""

    scenario_id: str
    shock_type: StressShockType
    price_shift_pct: Decimal = Decimal("0")
    iv_shift_pct: Decimal = Decimal("0")
    time_decay_days: int = 0
    rate_shift_pct: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class StressTestResult:
    """Result of a stress test."""

    scenario_id: str
    stress_loss: Decimal
    shocked_price: Decimal
    shocked_iv: Decimal
