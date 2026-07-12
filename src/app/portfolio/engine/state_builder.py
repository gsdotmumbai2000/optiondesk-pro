"""Portfolio state builder."""

from dataclasses import replace
from decimal import Decimal

from app.portfolio.holdings.aggregator import HoldingAggregator
from app.portfolio.models.broker import BrokerPositionUpdate
from app.portfolio.models.cash import CashAccount
from app.portfolio.models.enums import AssetClass, PositionStatus
from app.portfolio.models.portfolio import Portfolio
from app.portfolio.models.positions import Position
from app.portfolio.models.transactions import Trade
from app.portfolio.positions.manager import PositionManager
from app.portfolio.transactions.ledger import TransactionLedger
from app.utils.uuid_helper import generate_uuid


class PortfolioStateBuilder:
    """Apply trades and broker updates to portfolio state."""

    def __init__(self) -> None:
        """Initialize builder."""
        self._positions = PositionManager()
        self._holdings = HoldingAggregator()
        self._ledger = TransactionLedger()

    def apply_trades(
        self,
        portfolio: Portfolio,
        trades: tuple[Trade, ...],
    ) -> Portfolio:
        """Apply trade executions to portfolio."""
        if not trades:
            return portfolio
        open_list = list(portfolio.open_positions)
        closed_list = list(portfolio.closed_positions)
        tx_list = list(portfolio.transactions)
        executed = list(portfolio.executed_orders)
        cash = portfolio.cash_account
        balance = cash.balance
        for trade in trades:
            tx = self._ledger.record_trade(trade)
            tx_list.append(tx)
            executed.append(trade)
            balance = self._adjust_cash(balance, trade)
            open_list, closed_list = self._apply_position(
                open_list,
                closed_list,
                trade,
            )
        holdings = self._holdings.from_positions(tuple(open_list))
        cash_h = self._holdings.cash_holding(balance, cash.currency)
        return replace(
            portfolio,
            cash_account=CashAccount(
                balance=balance,
                available=balance - cash.reserved,
                reserved=cash.reserved,
                currency=cash.currency,
            ),
            holdings=holdings + (cash_h,),
            open_positions=tuple(open_list),
            closed_positions=tuple(closed_list),
            executed_orders=tuple(executed),
            transactions=tuple(tx_list),
        )

    def apply_broker_updates(
        self,
        portfolio: Portfolio,
        updates: tuple[BrokerPositionUpdate, ...],
    ) -> Portfolio:
        """Sync positions from broker updates."""
        if not updates:
            return portfolio
        open_map = {p.symbol: p for p in portfolio.open_positions}
        for update in updates:
            existing = open_map.get(update.symbol)
            open_map[update.symbol] = Position(
                position_id=existing.position_id if existing else generate_uuid(),
                symbol=update.symbol,
                asset_class=update.asset_class,
                quantity=update.quantity,
                entry_price=update.average_price,
                current_price=update.average_price,
                status=PositionStatus.OPEN,
                opened_at=existing.opened_at if existing else update.updated_at,
            )
        open_list = tuple(open_map.values())
        holdings = self._holdings.from_positions(open_list)
        cash_h = self._holdings.cash_holding(
            portfolio.cash_account.balance,
            portfolio.cash_account.currency,
        )
        return replace(
            portfolio,
            holdings=holdings + (cash_h,),
            open_positions=open_list,
        )

    def _adjust_cash(self, balance: Decimal, trade: Trade) -> Decimal:
        notional = trade.price * Decimal(abs(trade.quantity))
        if trade.side.upper() == "BUY":
            return balance - notional - trade.fees
        return balance + notional - trade.fees

    def _apply_position(
        self,
        open_list: list[Position],
        closed_list: list[Position],
        trade: Trade,
    ) -> tuple[list[Position], list[Position]]:
        symbol = trade.symbol
        existing = next((p for p in open_list if p.symbol == symbol), None)
        if trade.side.upper() == "BUY":
            if existing:
                idx = open_list.index(existing)
                open_list[idx] = self._positions.scale_in(
                    existing,
                    trade.quantity,
                    trade.price,
                )
            else:
                open_list.append(
                    self._positions.open(
                        symbol,
                        AssetClass.STOCK,
                        trade.quantity,
                        trade.price,
                    )
                )
        elif existing:
            if trade.quantity >= existing.quantity:
                closed_list.append(self._positions.close(existing, trade.price))
                open_list.remove(existing)
            else:
                closed, remaining = self._positions.partial_close(
                    existing,
                    trade.quantity,
                    trade.price,
                )
                closed_list.append(closed)
                if remaining is None:
                    open_list.remove(existing)
                else:
                    idx = open_list.index(existing)
                    open_list[idx] = remaining
        return open_list, closed_list
