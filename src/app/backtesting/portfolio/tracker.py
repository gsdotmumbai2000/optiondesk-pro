"""Portfolio tracker."""

from decimal import Decimal

from app.backtesting.models.trades import Trade
from app.backtesting.portfolio.models import (
    ClosedPosition,
    OpenPosition,
    PortfolioSnapshot,
)
from app.utils.uuid_helper import generate_uuid


class PortfolioTracker:
    """Track positions, PnL, cash, and margin during simulation."""

    def __init__(self, initial_capital: Decimal) -> None:
        """Initialize portfolio."""
        self._cash = initial_capital
        self._initial = initial_capital
        self._margin_usage = Decimal("0")
        self._open: list[OpenPosition] = []
        self._closed: list[ClosedPosition] = []
        self._realized = Decimal("0")
        self._unrealized = Decimal("0")

    def apply_trade(self, trade: Trade) -> None:
        """Apply executed trade to portfolio."""
        cost = trade.price * Decimal(trade.quantity) + trade.commission
        if trade.side.value == "BUY":
            self._cash -= cost
        else:
            self._cash += cost - trade.commission
        self._realized += trade.pnl

    def snapshot(self) -> PortfolioSnapshot:
        """Return current portfolio snapshot."""
        equity = self._cash + self._unrealized
        return PortfolioSnapshot(
            cash_balance=self._cash,
            margin_usage=self._margin_usage,
            open_positions=tuple(self._open),
            closed_positions=tuple(self._closed),
            realized_pnl=self._realized,
            unrealized_pnl=self._unrealized,
            equity=equity,
        )

    def update_margin(self, margin: Decimal) -> None:
        """Update margin usage from margin engine output."""
        self._margin_usage = margin

    def update_unrealized(self, pnl: Decimal) -> None:
        """Update unrealized PnL from engine output."""
        self._unrealized = pnl

    @property
    def initial_capital(self) -> Decimal:
        """Return initial capital."""
        return self._initial
