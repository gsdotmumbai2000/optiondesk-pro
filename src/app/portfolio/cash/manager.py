"""Cash account manager."""

from decimal import Decimal

from app.portfolio.models.cash import CashAccount


class CashManager:
    """Manage cash balances."""

    def __init__(self, initial: Decimal, currency: str = "INR") -> None:
        """Initialize cash manager."""
        self._balance = initial
        self._reserved = Decimal("0")
        self._currency = currency

    def account(self) -> CashAccount:
        """Return current cash account."""
        return CashAccount(
            balance=self._balance,
            available=self._balance - self._reserved,
            reserved=self._reserved,
            currency=self._currency,
        )

    def credit(self, amount: Decimal) -> None:
        """Credit cash."""
        self._balance += amount

    def debit(self, amount: Decimal) -> None:
        """Debit cash."""
        self._balance -= amount

    def reserve(self, amount: Decimal) -> None:
        """Reserve cash for margin."""
        self._reserved += amount

    def release(self, amount: Decimal) -> None:
        """Release reserved cash."""
        self._reserved = max(self._reserved - amount, Decimal("0"))
