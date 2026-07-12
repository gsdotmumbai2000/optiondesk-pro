"""Simulation configuration models."""

from dataclasses import dataclass
from decimal import Decimal

from app.backtesting.models.enums import OrderType, ReplaySpeed


@dataclass(frozen=True, slots=True)
class ReplayConfig:
    """Replay engine configuration."""

    speed: ReplaySpeed = ReplaySpeed.X1
    step_size: int = 1
    start_index: int = 0
    end_index: int | None = None


@dataclass(frozen=True, slots=True)
class ExecutionConfig:
    """Execution simulator configuration."""

    slippage_pct: Decimal = Decimal("0.05")
    commission_per_trade: Decimal = Decimal("20")
    brokerage_pct: Decimal = Decimal("0.03")
    exchange_charges_pct: Decimal = Decimal("0.01")
    latency_ms: int = 50
    partial_fill_enabled: bool = True
    default_order_type: OrderType = OrderType.MARKET


@dataclass(frozen=True, slots=True)
class SimulationParameters:
    """Full simulation parameters."""

    initial_capital: Decimal
    replay: ReplayConfig
    execution: ExecutionConfig
    max_positions: int = 100
