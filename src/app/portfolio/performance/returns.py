"""Return calculators from portfolio value series."""

from decimal import Decimal


class ReturnCalculator:
    """Compute period returns from value snapshots."""

    def period_return(self, start: Decimal, end: Decimal) -> Decimal:
        """Return fractional change between two values."""
        if start <= 0:
            return Decimal("0")
        return (end - start) / start

    def daily_return(
        self,
        values: tuple[Decimal, ...],
    ) -> Decimal:
        """Compute latest daily return."""
        if len(values) < 2:
            return Decimal("0")
        return self.period_return(values[-2], values[-1])

    def weekly_return(self, values: tuple[Decimal, ...]) -> Decimal:
        """Compute return over last 5 observations."""
        if len(values) < 6:
            return self.daily_return(values)
        return self.period_return(values[-6], values[-1])

    def monthly_return(self, values: tuple[Decimal, ...]) -> Decimal:
        """Compute return over last 21 observations."""
        if len(values) < 22:
            return self.weekly_return(values)
        return self.period_return(values[-22], values[-1])

    def annual_return(self, values: tuple[Decimal, ...]) -> Decimal:
        """Compute return over last 252 observations."""
        if len(values) < 2:
            return Decimal("0")
        start_idx = max(0, len(values) - 253)
        return self.period_return(values[start_idx], values[-1])
