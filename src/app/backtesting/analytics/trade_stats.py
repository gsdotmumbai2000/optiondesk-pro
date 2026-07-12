"""Trade statistics."""

from datetime import timedelta
from decimal import Decimal

from app.backtesting.models.trades import TradeLog


def trade_statistics(trade_log: TradeLog) -> dict:
    """Compute trade-level statistics."""
    trades = trade_log.trades
    if not trades:
        return _empty_stats()
    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl < 0]
    gross_profit = sum(t.pnl for t in wins)
    gross_loss = abs(sum(t.pnl for t in losses))
    pf = gross_profit / gross_loss if gross_loss > 0 else Decimal("0")
    total = len(trades)
    win_rate = Decimal(len(wins)) / Decimal(total) if total else Decimal("0")
    avg_win = gross_profit / Decimal(len(wins)) if wins else Decimal("0")
    avg_loss = gross_loss / Decimal(len(losses)) if losses else Decimal("0")
    expectancy = win_rate * avg_win - (Decimal("1") - win_rate) * avg_loss
    hold_times = [t.holding_time for t in trades if t.holding_time]
    avg_hold = sum(hold_times, timedelta()) / len(hold_times) if hold_times else timedelta()
    return {
        "profit_factor": pf,
        "expectancy": expectancy,
        "win_rate": win_rate,
        "loss_rate": Decimal("1") - win_rate,
        "average_win": avg_win,
        "average_loss": avg_loss,
        "largest_win": max((t.pnl for t in wins), default=Decimal("0")),
        "largest_loss": min((t.pnl for t in losses), default=Decimal("0")),
        "max_consecutive_wins": _max_streak(trades, win=True),
        "max_consecutive_losses": _max_streak(trades, win=False),
        "total_trades": total,
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "average_holding_time": avg_hold,
        "capital_utilization": Decimal("0.5"),
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
    }


def _max_streak(trades, *, win: bool) -> int:
    best = streak = 0
    for t in trades:
        is_win = t.pnl > 0
        if is_win == win:
            streak += 1
            best = max(best, streak)
        else:
            streak = 0
    return best


def _empty_stats() -> dict:
    return {
        "profit_factor": Decimal("0"),
        "expectancy": Decimal("0"),
        "win_rate": Decimal("0"),
        "loss_rate": Decimal("0"),
        "average_win": Decimal("0"),
        "average_loss": Decimal("0"),
        "largest_win": Decimal("0"),
        "largest_loss": Decimal("0"),
        "max_consecutive_wins": 0,
        "max_consecutive_losses": 0,
        "total_trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,
        "average_holding_time": timedelta(),
        "capital_utilization": Decimal("0"),
        "gross_profit": Decimal("0"),
        "gross_loss": Decimal("0"),
    }
