"""Position application service."""

from decimal import Decimal

from app.portfolio.models.enums import AssetClass
from app.portfolio.models.positions import Position
from app.portfolio.positions.manager import PositionManager


class PositionService:
    """Expose position lifecycle operations."""

    def __init__(self, manager: PositionManager | None = None) -> None:
        """Initialize service."""
        self._manager = manager or PositionManager()

    def open(
        self,
        symbol: str,
        asset_class: AssetClass,
        quantity: int,
        entry_price: Decimal,
    ) -> Position:
        """Open position."""
        return self._manager.open(symbol, asset_class, quantity, entry_price)

    def close(self, position: Position, exit_price: Decimal) -> Position:
        """Close position."""
        return self._manager.close(position, exit_price)

    def partial_close(
        self,
        position: Position,
        close_qty: int,
        exit_price: Decimal,
    ) -> tuple[Position, Position | None]:
        """Partially close position."""
        return self._manager.partial_close(position, close_qty, exit_price)

    def reverse(
        self,
        position: Position,
        price: Decimal,
    ) -> tuple[Position, Position]:
        """Reverse position."""
        return self._manager.reverse(position, price)

    def scale_in(self, position: Position, qty: int, price: Decimal) -> Position:
        """Scale into position."""
        return self._manager.scale_in(position, qty, price)

    def scale_out(
        self,
        position: Position,
        qty: int,
        price: Decimal,
    ) -> tuple[Position, Position | None]:
        """Scale out of position."""
        return self._manager.scale_out(position, qty, price)

    def roll(
        self,
        position: Position,
        new_symbol: str,
        exit_price: Decimal,
        entry_price: Decimal,
    ) -> tuple[Position, Position]:
        """Roll position."""
        return self._manager.roll(position, new_symbol, exit_price, entry_price)
