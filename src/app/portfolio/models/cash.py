"""Cash account model."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CashAccount:
    """Immutable cash account state."""

    balance: Decimal
    available: Decimal
    reserved: Decimal
    currency: str = "INR"
