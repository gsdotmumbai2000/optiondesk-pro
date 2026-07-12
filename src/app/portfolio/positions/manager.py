"""Position lifecycle manager."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

from app.portfolio.models.enums import AssetClass, PositionStatus
from app.portfolio.models.positions import Position
from app.utils.uuid_helper import generate_uuid


class PositionManager:
    """Manage position open, close, scale, and roll operations."""

    def open(
        self,
        symbol: str,
        asset_class: AssetClass,
        quantity: int,
        entry_price: Decimal,
    ) -> Position:
        """Open a new position."""
        return Position(
            position_id=generate_uuid(),
            symbol=symbol,
            asset_class=asset_class,
            quantity=quantity,
            entry_price=entry_price,
            current_price=entry_price,
            status=PositionStatus.OPEN,
            opened_at=datetime.now(timezone.utc),
        )

    def close(self, position: Position, exit_price: Decimal) -> Position:
        """Close an open position."""
        pnl = (exit_price - position.entry_price) * Decimal(position.quantity)
        return replace(
            position,
            status=PositionStatus.CLOSED,
            current_price=exit_price,
            closed_at=datetime.now(timezone.utc),
            realized_pnl=pnl,
            unrealized_pnl=Decimal("0"),
        )

    def partial_close(
        self,
        position: Position,
        close_qty: int,
        exit_price: Decimal,
    ) -> tuple[Position, Position | None]:
        """Partially close a position."""
        if close_qty >= position.quantity:
            return self.close(position, exit_price), None
        closed = replace(
            position,
            position_id=generate_uuid(),
            quantity=close_qty,
            status=PositionStatus.CLOSED,
            current_price=exit_price,
            closed_at=datetime.now(timezone.utc),
            realized_pnl=(exit_price - position.entry_price) * Decimal(close_qty),
        )
        remaining = replace(
            position,
            quantity=position.quantity - close_qty,
            status=PositionStatus.PARTIAL,
        )
        return closed, remaining

    def reverse(self, position: Position, price: Decimal) -> tuple[Position, Position]:
        """Reverse position direction."""
        closed = self.close(position, price)
        opened = self.open(
            position.symbol,
            position.asset_class,
            -position.quantity,
            price,
        )
        return closed, opened

    def scale_in(self, position: Position, qty: int, price: Decimal) -> Position:
        """Add to existing position."""
        new_qty = position.quantity + qty
        avg = (
            position.entry_price * Decimal(position.quantity) + price * Decimal(qty)
        ) / Decimal(new_qty)
        return replace(position, quantity=new_qty, entry_price=avg, current_price=price)

    def scale_out(
        self,
        position: Position,
        qty: int,
        price: Decimal,
    ) -> tuple[Position, Position | None]:
        """Reduce position size."""
        return self.partial_close(position, qty, price)

    def roll(
        self,
        position: Position,
        new_symbol: str,
        exit_price: Decimal,
        entry_price: Decimal,
    ) -> tuple[Position, Position]:
        """Roll position to new symbol."""
        closed = self.close(position, exit_price)
        opened = self.open(
            new_symbol,
            position.asset_class,
            position.quantity,
            entry_price,
        )
        return closed, opened
