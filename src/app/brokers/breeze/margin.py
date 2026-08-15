"""Breeze margin calculator service."""

from app.brokers.breeze.client_port import BreezeClientPort
from app.brokers.breeze.normalizers.margin_normalizer import normalize_margin
from app.brokers.breeze.utilities import (map_order_side, map_product_type,
                                          unwrap_success)
from app.brokers.shared.models import OrderRequest
from app.brokers.shared.models.portfolio import Margins


class BreezeMargin:
    """Pre-trade SPAN + exposure margin lookup via Breeze."""

    def __init__(self, client: BreezeClientPort) -> None:
        """Initialize margin service."""
        self._client = client

    def calculate_margin(
        self, positions: list[OrderRequest], exchange_code: str
    ) -> Margins:
        """Return normalized margin for a basket of positions."""
        payload = [self._position_payload(order) for order in positions]
        response = self._client.margin_calculator(payload, exchange_code.lower())
        return normalize_margin(unwrap_success(response), exchange_code)

    @staticmethod
    def _position_payload(order: OrderRequest) -> dict[str, str]:
        """Build one Breeze margin_calculator list_of_positions entry."""
        return {
            "strike_price": str(order.strike_price or ""),
            "quantity": str(order.quantity),
            "right": (order.option_right or "").lower(),
            "product": map_product_type(order.product_type),
            "action": map_order_side(order.side),
            "price": str(order.price or ""),
            "expiry_date": order.expiry_date or "",
            "stock_code": order.symbol,
            "cover_order_flow": "",
            "fresh_order_type": "",
            "cover_limit_rate": "",
            "cover_sltp_price": "",
            "fresh_limit_rate": "",
            "open_quantity": "",
        }
