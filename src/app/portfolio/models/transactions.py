"""Trade and transaction models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.portfolio.models.enums import TransactionType


@dataclass(frozen=True, slots=True)
class Trade:
    """Executed trade record."""

    trade_id: str
    symbol: str
    quantity: int
    price: Decimal
    side: str
    executed_at: datetime
    fees: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class Transaction:
    """Portfolio transaction ledger entry."""

    transaction_id: str
    transaction_type: TransactionType
    symbol: str
    quantity: int
    amount: Decimal
    fees: Decimal
    taxes: Decimal
    timestamp: datetime
    description: str = ""
