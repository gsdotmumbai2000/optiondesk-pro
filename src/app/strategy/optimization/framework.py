"""Optimization framework (no algorithms yet)."""

from dataclasses import dataclass

from app.strategy.models.enums import OptimizationGoal
from app.strategy.models.strategy import Strategy


@dataclass(frozen=True, slots=True)
class OptimizationRequest:
    """Future optimization request."""

    strategy: Strategy
    goal: OptimizationGoal
    constraints: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    """Placeholder optimization result."""

    goal: OptimizationGoal
    status: str
    message: str


class OptimizationFramework:
    """Framework for future strategy optimization."""

    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        """Return framework placeholder (no algorithm yet)."""
        return OptimizationResult(
            goal=request.goal,
            status="NOT_IMPLEMENTED",
            message=f"Optimization for {request.goal.value} is not yet available",
        )

    def supported_goals(self) -> tuple[OptimizationGoal, ...]:
        """Return supported optimization goals."""
        return tuple(OptimizationGoal)
