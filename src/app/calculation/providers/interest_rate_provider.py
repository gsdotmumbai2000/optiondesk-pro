"""Interest rate provider."""

from decimal import Decimal

from app.calculation.utilities.normalize_utils import normalize_interest_rate


class InterestRateProvider:
    """Supply interest and risk-free rates."""

    def __init__(
        self,
        *,
        risk_free_rate: Decimal = Decimal("0.065"),
        interest_rate: Decimal | None = None,
    ) -> None:
        """Initialize default rates."""
        self._risk_free_rate = normalize_interest_rate(risk_free_rate)
        self._interest_rate = normalize_interest_rate(
            interest_rate if interest_rate is not None else risk_free_rate
        )

    def interest_rate(self) -> Decimal:
        """Return interest rate."""
        return self._interest_rate

    def risk_free_rate(self) -> Decimal:
        """Return risk-free rate."""
        return self._risk_free_rate
