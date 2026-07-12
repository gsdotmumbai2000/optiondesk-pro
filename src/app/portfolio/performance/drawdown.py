"""Drawdown and recovery calculators."""

from decimal import Decimal


class DrawdownCalculator:
    """Compute drawdown and recovery from equity series."""

    def drawdown(self, values: tuple[Decimal, ...]) -> Decimal:
        """Return maximum drawdown as positive fraction."""
        if not values:
            return Decimal("0")
        peak = values[0]
        max_dd = Decimal("0")
        for value in values:
            if value > peak:
                peak = value
            if peak > 0:
                dd = (peak - value) / peak
                if dd > max_dd:
                    max_dd = dd
        return max_dd

    def recovery(self, values: tuple[Decimal, ...]) -> Decimal:
        """Return recovery ratio from trough to latest."""
        if len(values) < 2:
            return Decimal("0")
        trough = min(values)
        latest = values[-1]
        if trough <= 0:
            return Decimal("0")
        return (latest - trough) / trough
