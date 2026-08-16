"""Portfolio domain models."""

from decimal import Decimal

from pydantic import BaseModel, Field


class Position(BaseModel):
    """Normalized open position.

    `quantity` is signed: positive for a long (Buy) position, negative for
    a short (Sell) position -- matching the convention used elsewhere in
    this codebase (e.g. StrategyLeg.quantity), not Breeze's own raw
    response, which reports an always-positive quantity alongside a
    separate "action" field.
    """

    symbol: str
    exchange: str
    product_type: str
    quantity: int
    average_price: Decimal
    ltp: Decimal | None = None
    mtm: Decimal | None = None
    pnl: Decimal | None = None
    expiry_date: str | None = None
    strike_price: Decimal | None = None
    option_right: str | None = None


class Holding(BaseModel):
    """Normalized demat holding."""

    symbol: str
    exchange: str
    quantity: int
    average_price: Decimal
    current_price: Decimal | None = None
    pnl: Decimal | None = None


class Funds(BaseModel):
    """Normalized fund summary."""

    available_cash: Decimal = Decimal("0")
    used_margin: Decimal = Decimal("0")
    total_balance: Decimal = Decimal("0")
    currency: str = "INR"
    segments: dict[str, Decimal] = Field(default_factory=dict)


class Margins(BaseModel):
    """Normalized margin summary."""

    exchange: str
    span_margin: Decimal = Decimal("0")
    exposure_margin: Decimal = Decimal("0")
    additional_margin: Decimal = Decimal("0")
    total_margin: Decimal = Decimal("0")
