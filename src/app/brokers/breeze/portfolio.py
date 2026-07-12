"""Breeze portfolio service."""

from app.brokers.breeze.client_port import BreezeClientPort
from app.brokers.breeze.normalizers.portfolio_normalizer import (
    normalize_funds, normalize_holdings, normalize_positions,
    normalize_profile)
from app.brokers.shared.models import BrokerProfile, Funds, Holding, Position


class BreezePortfolio:
    """Fetch portfolio data from Breeze."""

    def __init__(self, client: BreezeClientPort, broker_code: str) -> None:
        """Initialize portfolio service."""
        self._client = client
        self._broker_code = broker_code

    def get_profile(self, session_token: str) -> BrokerProfile:
        """Return normalized profile."""
        response = self._client.get_customer_details(api_session=session_token)
        return normalize_profile(self._broker_code, response)

    def get_funds(self) -> Funds:
        """Return normalized funds."""
        return normalize_funds(self._client.get_funds())

    def get_holdings(self) -> list[Holding]:
        """Return normalized holdings."""
        return normalize_holdings(self._client.get_demat_holdings())

    def get_positions(self) -> list[Position]:
        """Return normalized positions."""
        return normalize_positions(self._client.get_portfolio_positions())
