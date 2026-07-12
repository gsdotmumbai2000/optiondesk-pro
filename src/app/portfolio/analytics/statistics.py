"""Portfolio statistics calculator."""

from decimal import Decimal

from app.portfolio.models.performance import PortfolioStatistics
from app.portfolio.models.positions import Position


class StatisticsCalculator:
    """Compute trade statistics from closed positions."""

    def calculate(
        self,
        closed_positions: tuple[Position, ...],
    ) -> PortfolioStatistics:
        """Build statistics from closed positions."""
        if not closed_positions:
            zero = Decimal("0")
            return PortfolioStatistics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=zero,
                average_trade_pnl=zero,
            )
        wins = [p for p in closed_positions if p.realized_pnl > 0]
        losses = [p for p in closed_positions if p.realized_pnl < 0]
        total = len(closed_positions)
        avg = sum(p.realized_pnl for p in closed_positions) / Decimal(total)
        return PortfolioStatistics(
            total_trades=total,
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate=Decimal(len(wins)) / Decimal(total),
            average_trade_pnl=avg,
        )
