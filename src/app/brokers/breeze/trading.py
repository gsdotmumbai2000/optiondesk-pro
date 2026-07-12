"""Breeze trading service."""

from datetime import datetime

from app.brokers.breeze.client_port import BreezeClientPort
from app.brokers.breeze.normalizers.order_normalizer import normalize_order
from app.brokers.breeze.utilities import (map_order_side, map_order_type,
                                          map_product_type, map_validity,
                                          unwrap_success)
from app.brokers.shared.enums import OrderValidity
from app.brokers.shared.models import Order, OrderModification, OrderRequest


class BreezeTrading:
    """Place and manage orders via Breeze."""

    def __init__(self, client: BreezeClientPort) -> None:
        """Initialize trading service."""
        self._client = client

    def get_orders(
        self,
        exchange: str,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[Order]:
        """Return normalized orders."""
        response = self._client.get_order_list(
            exchange_code=exchange.lower(),
            from_date=(from_date or datetime.now()).strftime("%Y-%m-%d"),
            to_date=(to_date or datetime.now()).strftime("%Y-%m-%d"),
        )
        payload = unwrap_success(response)
        rows = payload if isinstance(payload, list) else []
        return [normalize_order(row) for row in rows]

    def place_order(self, request: OrderRequest) -> Order:
        """Place order and return normalized result."""
        order_type, stoploss = map_order_type(request.order_type)
        response = self._client.place_order(
            stock_code=request.symbol,
            exchange_code=request.exchange.lower(),
            product=map_product_type(request.product_type),
            action=map_order_side(request.side),
            order_type=order_type,
            stoploss=stoploss,
            quantity=str(request.quantity),
            price=str(request.price or ""),
            validity=map_validity(request.validity),
            expiry_date=request.expiry_date or "",
            right=(request.option_right or "").lower(),
            strike_price=str(request.strike_price or ""),
            user_remark=request.user_remark,
        )
        return normalize_order(unwrap_success(response))

    def modify_order(self, modification: OrderModification) -> Order:
        """Modify order and return normalized result."""
        order_type = ""
        stoploss = ""
        if modification.order_type is not None:
            order_type, stoploss = map_order_type(modification.order_type)
        response = self._client.modify_order(
            order_id=modification.order_id,
            exchange_code=modification.exchange.lower(),
            order_type=order_type,
            stoploss=stoploss,
            quantity=str(modification.quantity or ""),
            price=str(modification.price or ""),
            validity=map_validity(modification.validity or OrderValidity.DAY),
            disclosed_quantity=str(modification.disclosed_quantity or ""),
            validity_date="",
        )
        return normalize_order(unwrap_success(response))

    def cancel_order(self, exchange: str, order_id: str) -> Order:
        """Cancel order and return normalized result."""
        response = self._client.cancel_order(
            exchange_code=exchange.lower(),
            order_id=order_id,
        )
        return normalize_order(unwrap_success(response))
