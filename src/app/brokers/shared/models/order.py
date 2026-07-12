"""Order domain models."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.brokers.shared.enums import (OrderSide, OrderType, OrderValidity,
                                      ProductType)


class OrderRequest(BaseModel):
    """Unified order placement request."""

    symbol: str
    exchange: str
    product_type: ProductType
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Decimal | None = None
    trigger_price: Decimal | None = None
    validity: OrderValidity = OrderValidity.DAY
    disclosed_quantity: int | None = None
    expiry_date: str | None = None
    strike_price: Decimal | None = None
    option_right: str | None = None
    user_remark: str = ""


class OrderModification(BaseModel):
    """Unified order modification request."""

    order_id: str
    exchange: str
    order_type: OrderType | None = None
    quantity: int | None = None
    price: Decimal | None = None
    trigger_price: Decimal | None = None
    validity: OrderValidity | None = None
    disclosed_quantity: int | None = None


class Order(BaseModel):
    """Normalized order record."""

    order_id: str
    exchange: str
    symbol: str
    product_type: ProductType
    side: OrderSide
    order_type: OrderType
    quantity: int
    filled_quantity: int = 0
    price: Decimal | None = None
    trigger_price: Decimal | None = None
    status: str
    validity: OrderValidity = OrderValidity.DAY
    order_time: datetime | None = None
    user_remark: str = ""
