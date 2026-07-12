"""Volatility provider."""

from decimal import Decimal

from app.calculation.utilities.normalize_utils import normalize_volatility


class VolatilityProvider:
    """Supply volatility inputs."""

    def __init__(
        self,
        *,
        volatility: Decimal | None = None,
        historical_volatility: Decimal | None = None,
        implied_volatility: Decimal | None = None,
    ) -> None:
        """Initialize volatility defaults."""
        base = volatility or implied_volatility or historical_volatility or Decimal("0.20")
        self._volatility = normalize_volatility(base)
        self._historical = (
            normalize_volatility(historical_volatility)
            if historical_volatility is not None
            else None
        )
        self._implied = (
            normalize_volatility(implied_volatility)
            if implied_volatility is not None
            else None
        )

    def volatility(self) -> Decimal:
        """Return primary volatility."""
        return self._volatility

    def historical_volatility(self) -> Decimal | None:
        """Return historical volatility."""
        return self._historical

    def implied_volatility(self) -> Decimal | None:
        """Return implied volatility."""
        return self._implied

    def from_option_chain(self, atm_iv: Decimal | None) -> "VolatilityProvider":
        """Return provider with implied vol from chain."""
        implied = atm_iv if atm_iv is not None else self._implied
        return VolatilityProvider(
            volatility=implied or self._volatility,
            historical_volatility=self._historical,
            implied_volatility=implied,
        )
