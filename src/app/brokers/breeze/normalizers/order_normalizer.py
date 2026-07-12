"""Normalize Breeze order responses."""

from datetime import datetime
from typing import Any

from app.brokers.breeze.utilities import to_decimal, to_int
from app.brokers.shared.enums import (OrderSide, OrderType, OrderValidity,
                                      ProductType)
from app.brokers.shared.models import Order


def normalize_order(payload: Any) -> Order:
    """Convert Breeze order payload to domain Order."""
    data = payload[0] if isinstance(payload, list) and payload else payload
    if not isinstance(data, dict):
        data = {}
    return Order(
        order_id=str(data.get("order_id", "")),
        exchange=str(data.get("exchange_code", "")),
        symbol=str(data.get("stock_code", "")),
        product_type=_product(data.get("product_type")),
        side=_side(data.get("action")),
        order_type=_order_type(data.get("order_type")),
        quantity=to_int(data.get("quantity")) or 0,
        filled_quantity=to_int(data.get("quantity_filled")) or 0,
        price=to_decimal(data.get("price")),
        trigger_price=to_decimal(data.get("stoploss")),
        status=str(data.get("status", "")),
        validity=_validity(data.get("validity")),
        order_time=datetime.now(),
        user_remark=str(data.get("user_remark", "")),
    )


def _product(value: Any) -> ProductType:
    text = str(value or "cash").lower()
    if text == "futures":
        return ProductType.FUTURES
    if text == "options":
        return ProductType.OPTIONS
    return ProductType.CASH


def _side(value: Any) -> OrderSide:
    return OrderSide.BUY if str(value).lower() == "buy" else OrderSide.SELL


def _order_type(value: Any) -> OrderType:
    text = str(value or "limit").lower()
    if text == "market":
        return OrderType.MARKET
    if text == "stoploss":
        return OrderType.STOP_LOSS
    return OrderType.LIMIT


def _validity(value: Any) -> OrderValidity:
    text = str(value or "day").lower()
    if text == "ioc":
        return OrderValidity.IOC
    if text == "vtc":
        return OrderValidity.GTC
    return OrderValidity.DAY
