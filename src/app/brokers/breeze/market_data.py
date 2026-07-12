"""Breeze market data service."""

from app.brokers.breeze.client_port import BreezeClientPort
from app.brokers.breeze.normalizers.quote_normalizer import normalize_quote
from app.brokers.breeze.utilities import unwrap_success
from app.brokers.shared.models import Quote


class BreezeMarketData:
    """Fetch live quotes from Breeze."""

    def __init__(self, client: BreezeClientPort) -> None:
        """Initialize market data service."""
        self._client = client

    def get_quotes(
        self,
        symbol: str,
        exchange: str,
        *,
        expiry_date: str = "",
        product_type: str = "",
        option_right: str = "",
        strike_price: str = "",
    ) -> Quote:
        """Return normalized quote."""
        response = self._client.get_quotes(
            stock_code=symbol,
            exchange_code=exchange.lower(),
            expiry_date=expiry_date,
            product_type=product_type.lower(),
            right=option_right.lower(),
            strike_price=strike_price,
        )
        payload = unwrap_success(response)
        return normalize_quote(symbol, exchange, payload)
