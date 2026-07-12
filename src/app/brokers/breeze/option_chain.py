"""Breeze option chain service."""

from decimal import Decimal

from app.brokers.breeze.client_port import BreezeClientPort
from app.brokers.breeze.normalizers.option_chain_normalizer import \
    normalize_option_chain
from app.brokers.breeze.utilities import unwrap_success
from app.brokers.shared.models import OptionChain, OptionChainRequest


class BreezeOptionChain:
    """Fetch option chain data from Breeze."""

    def __init__(self, client: BreezeClientPort) -> None:
        """Initialize option chain service."""
        self._client = client

    def get_option_chain(
        self,
        request: OptionChainRequest,
        *,
        spot_price: Decimal | None = None,
        atm_strike: Decimal | None = None,
    ) -> OptionChain:
        """Return normalized option chain."""
        response = self._client.get_option_chain_quotes(
            stock_code=request.underlying,
            exchange_code=request.exchange.lower(),
            expiry_date=request.expiry_date,
            product_type="options",
            right=(request.right.value.lower() if request.right else ""),
            strike_price=str(request.strike_price or ""),
        )
        payload = unwrap_success(response)
        return normalize_option_chain(
            request.underlying,
            request.exchange,
            request.expiry_date,
            payload,
            spot_price=spot_price,
            atm_strike=atm_strike,
        )
