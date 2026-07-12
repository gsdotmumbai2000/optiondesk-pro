"""Execution service."""

from app.backtesting.execution.simulator import (
    ExecutionResult,
    ExecutionSimulator,
    OrderRequest,
)
from app.backtesting.models.config import ExecutionConfig


class ExecutionService:
    """Manage execution simulation."""

    def create(self, config: ExecutionConfig) -> ExecutionSimulator:
        """Create execution simulator."""
        return ExecutionSimulator(config)

    def execute(
        self,
        simulator: ExecutionSimulator,
        order: OrderRequest,
    ) -> ExecutionResult:
        """Execute order via simulator."""
        return simulator.execute(order)
