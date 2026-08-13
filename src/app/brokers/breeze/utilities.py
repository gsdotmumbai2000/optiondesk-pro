"""Breeze utility helpers."""

from decimal import Decimal, InvalidOperation
from typing import Any

from app.brokers.shared.enums import (HistoricalInterval, OrderSide, OrderType,
                                      OrderValidity, ProductType)
from app.brokers.shared.exceptions import BrokerNotSupportedException
from app.exceptions.broker_exception import BrokerException


def to_decimal(value: Any) -> Decimal | None:
    """Safely convert a value to Decimal."""
    if value in (None, "", "NA"):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def to_int(value: Any) -> int | None:
    """Safely convert a value to int."""
    if value in (None, "", "NA"):
        return None
    try:
        return int(str(value).split(".")[0])
    except ValueError:
        return None


def map_product_type(product: ProductType) -> str:
    """Map unified product type to Breeze product string."""
    mapping = {
        ProductType.CASH: "cash",
        ProductType.FUTURES: "futures",
        ProductType.OPTIONS: "options",
        ProductType.CURRENCY: "futures",
        ProductType.COMMODITY: "futures",
    }
    return mapping[product]


def map_order_side(side: OrderSide) -> str:
    """Map order side to Breeze action."""
    return side.value.lower()


def map_order_type(order_type: OrderType) -> tuple[str, str]:
    """Map unified order type to Breeze order_type and stoploss."""
    if order_type == OrderType.MARKET:
        return "market", ""
    if order_type == OrderType.LIMIT:
        return "limit", ""
    if order_type == OrderType.STOP_LOSS:
        return "stoploss", "Y"
    if order_type == OrderType.STOP_LOSS_MARKET:
        return "stoploss", "Y"
    raise BrokerNotSupportedException(
        f"Order type not supported on Breeze: {order_type}"
    )


def map_validity(validity: OrderValidity) -> str:
    """Map order validity to Breeze validity."""
    mapping = {
        OrderValidity.DAY: "day",
        OrderValidity.IOC: "ioc",
        OrderValidity.GTC: "vtc",
    }
    return mapping[validity]


def map_historical_interval(interval: HistoricalInterval) -> str:
    """Map unified interval to Breeze historical v2 interval."""
    supported = {
        HistoricalInterval.ONE_MINUTE: "1minute",
        HistoricalInterval.FIVE_MINUTE: "5minute",
        HistoricalInterval.THIRTY_MINUTE: "30minute",
        HistoricalInterval.ONE_DAY: "1day",
    }
    if interval not in supported:
        raise BrokerNotSupportedException(
            f"Interval {interval.value} is not supported by Breeze historical API"
        )
    return supported[interval]


def unwrap_success(response: dict[str, Any]) -> Any:
    """Extract Success payload or raise with Error.

    Breeze's response envelope always includes an "Error" key, set to None
    on success (e.g. {"Success": [...], "Status": 200, "Error": None}), so
    checking key presence rejects every successful response. The Error
    value's truthiness is what actually indicates a failure.
    """
    error = response.get("Error")
    if error:
        raise BrokerException(str(error))
    return response.get("Success", response)
