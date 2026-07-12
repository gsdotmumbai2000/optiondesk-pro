"""Holdings aggregator."""

from decimal import Decimal

from app.portfolio.models.enums import AssetClass
from app.portfolio.models.positions import Holding, Position
from app.utils.uuid_helper import generate_uuid


class HoldingAggregator:
    """Aggregate positions into holdings."""

    def from_positions(self, positions: tuple[Position, ...]) -> tuple[Holding, ...]:
        """Build holdings from open positions."""
        buckets: dict[str, list[Position]] = {}
        for pos in positions:
            buckets.setdefault(pos.symbol, []).append(pos)
        holdings: list[Holding] = []
        for symbol, group in buckets.items():
            qty = sum(p.quantity for p in group)
            avg = sum(p.entry_price * Decimal(p.quantity) for p in group) / Decimal(qty)
            mv = sum(p.current_price * Decimal(p.quantity) for p in group)
            upnl = sum(p.unrealized_pnl for p in group)
            holdings.append(
                Holding(
                    holding_id=generate_uuid(),
                    symbol=symbol,
                    asset_class=group[0].asset_class,
                    quantity=qty,
                    average_price=avg,
                    market_value=mv,
                    unrealized_pnl=upnl,
                )
            )
        return tuple(holdings)

    def cash_holding(self, balance: Decimal, currency: str = "INR") -> Holding:
        """Create cash holding."""
        return Holding(
            holding_id=generate_uuid(),
            symbol=currency,
            asset_class=AssetClass.CASH,
            quantity=1,
            average_price=balance,
            market_value=balance,
            unrealized_pnl=Decimal("0"),
        )
