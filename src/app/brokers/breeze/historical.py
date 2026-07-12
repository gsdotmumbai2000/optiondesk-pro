"""Breeze historical data service."""

from app.brokers.breeze.client_port import BreezeClientPort
from app.brokers.breeze.normalizers.historical_normalizer import \
    normalize_historical
from app.brokers.breeze.utilities import (map_historical_interval,
                                          map_product_type, unwrap_success)
from app.brokers.shared.models import HistoricalBar, HistoricalRequest


class BreezeHistorical:
    """Fetch historical data from Breeze."""

    def __init__(self, client: BreezeClientPort) -> None:
        """Initialize historical service."""
        self._client = client

    def get_historical_data(self, request: HistoricalRequest) -> list[HistoricalBar]:
        """Return normalized historical bars."""
        response = self._client.get_historical_data_v2(
            interval=map_historical_interval(request.interval),
            from_date=request.from_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            to_date=request.to_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            stock_code=request.symbol,
            exchange_code=request.exchange.lower(),
            product_type=map_product_type(request.product_type),
            expiry_date=request.expiry_date or "",
            right=(request.option_right or "").lower(),
            strike_price=str(request.strike_price or ""),
        )
        payload = unwrap_success(response)
        return normalize_historical(payload)
