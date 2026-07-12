"""Execution simulator."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from app.backtesting.models.config import ExecutionConfig
from app.backtesting.models.enums import OrderSide, OrderType
from app.backtesting.models.trades import Trade
from app.utils.uuid_helper import generate_uuid


@dataclass(frozen=True, slots=True)
class OrderRequest:
    """Simulated order request."""

    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Decimal
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Simulated execution result."""

    trade: Trade
    filled_quantity: int
    fill_price: Decimal
    latency_applied: timedelta


class ExecutionSimulator:
    """Simulate order execution with slippage and fees."""

    def __init__(self, config: ExecutionConfig) -> None:
        """Initialize simulator."""
        self._config = config

    def execute(self, order: OrderRequest) -> ExecutionResult:
        """Execute a simulated order."""
        fill_price = self._apply_slippage(order.price, order.side)
        filled_qty = self._resolve_fill(order.quantity)
        commission = self._compute_fees(fill_price, filled_qty)
        slippage = abs(fill_price - order.price)
        trade = Trade(
            trade_id=generate_uuid(),
            timestamp=order.timestamp,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=filled_qty,
            price=fill_price,
            commission=commission,
            slippage=slippage,
            pnl=Decimal("0"),
            holding_time=timedelta(0),
        )
        latency = timedelta(milliseconds=self._config.latency_ms)
        return ExecutionResult(
            trade=trade,
            filled_quantity=filled_qty,
            fill_price=fill_price,
            latency_applied=latency,
        )

    def _apply_slippage(self, price: Decimal, side: OrderSide) -> Decimal:
        slip = price * self._config.slippage_pct / Decimal("100")
        if side == OrderSide.BUY:
            return price + slip
        return price - slip

    def _resolve_fill(self, quantity: int) -> int:
        if not self._config.partial_fill_enabled:
            return quantity
        return max(quantity - 1, 1) if quantity > 1 else quantity

    def _compute_fees(self, price: Decimal, qty: int) -> Decimal:
        notional = price * Decimal(qty)
        brokerage = notional * self._config.brokerage_pct / Decimal("100")
        exchange = notional * self._config.exchange_charges_pct / Decimal("100")
        return self._config.commission_per_trade + brokerage + exchange
