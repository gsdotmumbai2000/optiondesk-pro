"""Transaction ledger."""

from datetime import datetime
from decimal import Decimal

from app.portfolio.models.enums import TransactionType
from app.portfolio.models.transactions import Trade, Transaction
from app.utils.uuid_helper import generate_uuid


class TransactionLedger:
    """Maintain transaction history."""

    def __init__(self) -> None:
        """Initialize ledger."""
        self._transactions: list[Transaction] = []

    @property
    def transactions(self) -> tuple[Transaction, ...]:
        """Return all transactions."""
        return tuple(self._transactions)

    def record_trade(self, trade: Trade) -> Transaction:
        """Record trade as transaction."""
        tx_type = (
            TransactionType.BUY if trade.side.upper() == "BUY" else TransactionType.SELL
        )
        amount = trade.price * abs(trade.quantity)
        tx = Transaction(
            transaction_id=generate_uuid(),
            transaction_type=tx_type,
            symbol=trade.symbol,
            quantity=trade.quantity,
            amount=amount,
            fees=trade.fees,
            taxes=trade.fees * 0,  # placeholder
            timestamp=trade.executed_at,
            description=f"Trade {trade.trade_id}",
        )
        self._transactions.append(tx)
        return tx

    def record_fee(self, symbol: str, amount: Decimal, timestamp: datetime) -> Transaction:
        """Record fee transaction."""
        tx = Transaction(
            transaction_id=generate_uuid(),
            transaction_type=TransactionType.FEE,
            symbol=symbol,
            quantity=0,
            amount=Decimal(str(amount)),
            fees=Decimal(str(amount)),
            taxes=Decimal("0"),
            timestamp=timestamp,
            description="Broker fee",
        )
        self._transactions.append(tx)
        return tx
