"""Cash application service."""

from decimal import Decimal

from app.portfolio.cash.manager import CashManager
from app.portfolio.models.cash import CashAccount


class CashService:
    """Expose cash account operations."""

    def create(self, initial: Decimal, currency: str = "INR") -> CashManager:
        """Create cash manager."""
        return CashManager(initial, currency)

    def account(self, manager: CashManager) -> CashAccount:
        """Return cash account snapshot."""
        return manager.account()

    def credit(self, manager: CashManager, amount: Decimal) -> None:
        """Credit cash."""
        manager.credit(amount)

    def debit(self, manager: CashManager, amount: Decimal) -> None:
        """Debit cash."""
        manager.debit(amount)

    def reserve(self, manager: CashManager, amount: Decimal) -> None:
        """Reserve cash."""
        manager.reserve(amount)

    def release(self, manager: CashManager, amount: Decimal) -> None:
        """Release reserved cash."""
        manager.release(amount)
