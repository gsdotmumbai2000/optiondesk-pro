"""Simulated paper trading account: position netting and cash accounting
around real fills from the backtesting engine's ExecutionSimulator.
"""

from datetime import datetime
from decimal import Decimal

from app.backtesting.execution.simulator import ExecutionSimulator, OrderRequest
from app.backtesting.models.config import ExecutionConfig
from app.backtesting.models.enums import OrderSide, OrderType
from app.paper_trading.models.account import PaperAccountSnapshot, PaperPosition, PaperTrade
from app.paper_trading.models.request import PaperOrderRequest
from app.strategy.models.leg import StrategyLeg
from app.utils.uuid_helper import generate_uuid

_InstrumentKey = tuple[str, str, Decimal, object, str]


class PaperTradingAccount:
    """Track one virtual account's cash, open positions, and trade
    history. Equity is valued at each open position's own cost basis (no
    live mark-to-market): it reflects realized economics only --
    commissions paid and PnL already realized on closed portions -- and
    equals cash_balance whenever nothing is open. A live price feed could
    later mark positions to market; this module has no dependency on one.
    """

    def __init__(
        self,
        account_id: str,
        initial_capital: Decimal,
        execution_config: ExecutionConfig | None = None,
    ) -> None:
        self._account_id = account_id
        self._initial_capital = initial_capital
        self._cash = initial_capital
        self._realized_pnl = Decimal("0")
        self._positions: dict[_InstrumentKey, PaperPosition] = {}
        self._trades: list[PaperTrade] = []
        # partial_fill_enabled=False by default here even though
        # ExecutionConfig defaults it True: that default always fills
        # exactly one unit short (see ExecutionSimulator._resolve_fill()),
        # which suits historical replay's need to exercise the partial-fill
        # code path but is a confusing default for paper trading, where a
        # market order is expected to fill in full.
        self._executor = ExecutionSimulator(
            execution_config or ExecutionConfig(partial_fill_enabled=False)
        )

    def submit_order(self, request: PaperOrderRequest) -> PaperTrade:
        """Simulate a fill for `request` and update cash/positions/history."""
        order = OrderRequest(
            symbol=request.leg.underlying or "",
            side=request.side,
            order_type=OrderType.MARKET,
            quantity=request.quantity,
            price=request.reference_price,
            timestamp=request.timestamp,
        )
        result = self._executor.execute(order)
        fill_price = result.fill_price
        filled_qty = result.filled_quantity
        commission = result.trade.commission

        delta_qty = filled_qty if request.side == OrderSide.BUY else -filled_qty
        key = _instrument_key(request.leg)
        realized = self._apply_fill(key, request.leg, delta_qty, fill_price, request.timestamp)

        cash_flow = -fill_price * Decimal(filled_qty) if request.side == OrderSide.BUY else fill_price * Decimal(filled_qty)
        self._cash += cash_flow - commission
        self._realized_pnl += realized

        trade = PaperTrade(
            trade_id=generate_uuid(), leg=request.leg, side=request.side, quantity=filled_qty,
            fill_price=fill_price, commission=commission, slippage=result.trade.slippage,
            timestamp=request.timestamp, realized_pnl=realized,
        )
        self._trades.append(trade)
        return trade

    def snapshot(self) -> PaperAccountSnapshot:
        """Return current account state."""
        cost_basis = sum(
            (Decimal(p.quantity) * p.average_entry_price for p in self._positions.values()),
            Decimal("0"),
        )
        return PaperAccountSnapshot(
            account_id=self._account_id,
            initial_capital=self._initial_capital,
            cash_balance=self._cash,
            open_positions=tuple(self._positions.values()),
            realized_pnl=self._realized_pnl,
            equity=self._cash + cost_basis,
        )

    def trade_history(self) -> tuple[PaperTrade, ...]:
        """Return all trades executed on this account, oldest first."""
        return tuple(self._trades)

    def _apply_fill(
        self,
        key: _InstrumentKey,
        leg: StrategyLeg,
        delta_qty: int,
        fill_price: Decimal,
        timestamp: datetime,
    ) -> Decimal:
        """Update the position book for one fill: opens, adds to, partially
        closes, fully closes, or reverses the position for `key`. Returns
        realized PnL from whatever portion of `delta_qty` closed an
        existing position (0 when this fill only opens or adds)."""
        existing = self._positions.get(key)
        existing_qty = existing.quantity if existing is not None else 0
        existing_avg = existing.average_entry_price if existing is not None else Decimal("0")
        new_qty = existing_qty + delta_qty

        realized = Decimal("0")
        if existing_qty != 0 and _sign(delta_qty) != _sign(existing_qty):
            closed_qty = min(abs(existing_qty), abs(delta_qty))
            realized = Decimal(closed_qty) * (fill_price - existing_avg) * Decimal(_sign(existing_qty))

        if new_qty == 0:
            self._positions.pop(key, None)
            return realized

        if existing_qty == 0 or _sign(new_qty) != _sign(existing_qty):
            average_entry = fill_price  # fresh open, or reversal past flat
        elif _sign(delta_qty) == _sign(existing_qty):
            average_entry = (
                Decimal(existing_qty) * existing_avg + Decimal(delta_qty) * fill_price
            ) / Decimal(new_qty)  # adding to the position: weighted average
        else:
            average_entry = existing_avg  # partial close, same direction remains: entry unchanged

        self._positions[key] = PaperPosition(
            position_id=existing.position_id if existing is not None else generate_uuid(),
            leg=leg,
            quantity=new_qty,
            average_entry_price=average_entry,
            opened_at=existing.opened_at if existing is not None else timestamp,
        )
        return realized


def _instrument_key(leg: StrategyLeg) -> _InstrumentKey:
    """Identity of the instrument a leg trades -- deliberately excludes
    BUY/SELL direction (that's the order's side, not the instrument) and
    leg_id (a fresh UUID per StrategyLeg, so it can never match between an
    opening and a closing order for "the same" contract)."""
    kind_value = leg.kind.value
    if "CALL" in kind_value:
        right = "CALL"
    elif "PUT" in kind_value:
        right = "PUT"
    elif "FUTURE" in kind_value:
        right = "FUTURE"
    else:
        right = "STOCK"
    return (leg.underlying, leg.exchange, leg.strike, leg.expiry, right)


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)
