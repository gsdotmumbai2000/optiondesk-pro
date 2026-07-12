"""CAGR and return-on-capital calculators."""

from decimal import Decimal


class CagrCalculator:
    """Compute CAGR and return on capital."""

    def cagr(
        self,
        start_value: Decimal,
        end_value: Decimal,
        periods: int,
    ) -> Decimal:
        """Compute compound annual growth rate."""
        if start_value <= 0 or periods <= 0:
            return Decimal("0")
        growth = end_value / start_value
        # Approximate annualization for daily periods (252 trading days).
        exponent = Decimal("252") / Decimal(periods)
        return growth ** exponent - Decimal("1")

    def return_on_capital(
        self,
        net_profit: Decimal,
        capital_deployed: Decimal,
    ) -> Decimal:
        """Return profit relative to deployed capital."""
        if capital_deployed <= 0:
            return Decimal("0")
        return net_profit / capital_deployed
