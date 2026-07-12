"""Transaction application service."""

from app.portfolio.models.transactions import Trade, Transaction
from app.portfolio.transactions.ledger import TransactionLedger


class TransactionService:
    """Expose transaction ledger operations."""

    def __init__(self, ledger: TransactionLedger | None = None) -> None:
        """Initialize service."""
        self._ledger = ledger or TransactionLedger()

    @property
    def transactions(self) -> tuple[Transaction, ...]:
        """Return all transactions."""
        return self._ledger.transactions

    def record_trade(self, trade: Trade) -> Transaction:
        """Record trade."""
        return self._ledger.record_trade(trade)

    def record_fee(self, symbol: str, amount, timestamp) -> Transaction:
        """Record fee."""
        return self._ledger.record_fee(symbol, amount, timestamp)
