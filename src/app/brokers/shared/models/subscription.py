"""Quote subscription domain models."""

from pydantic import BaseModel

from app.brokers.shared.enums import ProductType, QuoteSubscriptionMode


class QuoteSubscription(BaseModel):
    """Quote subscription descriptor."""

    symbol: str
    exchange: str
    product_type: ProductType = ProductType.CASH
    expiry_date: str = ""
    strike_price: str = ""
    option_right: str = ""
    mode: QuoteSubscriptionMode = QuoteSubscriptionMode.FULL
    interval: str = ""
