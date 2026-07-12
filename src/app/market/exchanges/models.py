"""Exchange domain models and defaults."""

from decimal import Decimal

from pydantic import BaseModel

from app.market.enums import ExchangeCode


class Exchange(BaseModel):
    """Exchange reference record."""

    code: ExchangeCode
    name: str
    country_code: str = "IN"
    currency_code: str = "INR"
    timezone: str = "Asia/Kolkata"
    is_active: bool = True


class UnderlyingMaster(BaseModel):
    """Underlying index or asset master record."""

    symbol: str
    display_name: str
    exchange: ExchangeCode
    instrument_type: str
    lot_size: int
    tick_size: Decimal
    strike_interval: Decimal
    freeze_quantity: int
    price_precision: int = 2
    quantity_precision: int = 0
    contract_multiplier: int = 1
    weekly_expiry_day: str | None = None
    monthly_expiry_day: str | None = None
    segment: str = "FO"
    is_active: bool = True
    category: str = "INDEX"


DEFAULT_EXCHANGES: list[Exchange] = [
    Exchange(code=ExchangeCode.NSE, name="National Stock Exchange of India"),
    Exchange(code=ExchangeCode.BSE, name="BSE Limited"),
    Exchange(code=ExchangeCode.MCX, name="Multi Commodity Exchange of India"),
    Exchange(code=ExchangeCode.NSEFO, name="NSE Futures and Options"),
    Exchange(code=ExchangeCode.BSEFO, name="BSE Futures and Options"),
]

DEFAULT_UNDERLYINGS: list[UnderlyingMaster] = [
    UnderlyingMaster(
        symbol="NIFTY",
        display_name="NIFTY 50",
        exchange=ExchangeCode.NSEFO,
        instrument_type="INDEX",
        lot_size=25,
        tick_size=Decimal("0.05"),
        strike_interval=Decimal("50"),
        freeze_quantity=1800,
        weekly_expiry_day="TUESDAY",
        monthly_expiry_day="TUESDAY",
        category="INDEX",
    ),
    UnderlyingMaster(
        symbol="BANKNIFTY",
        display_name="NIFTY Bank",
        exchange=ExchangeCode.NSEFO,
        instrument_type="INDEX",
        lot_size=15,
        tick_size=Decimal("0.05"),
        strike_interval=Decimal("100"),
        freeze_quantity=900,
        weekly_expiry_day="WEDNESDAY",
        monthly_expiry_day="WEDNESDAY",
        category="INDEX",
    ),
    UnderlyingMaster(
        symbol="FINNIFTY",
        display_name="NIFTY Financial Services",
        exchange=ExchangeCode.NSEFO,
        instrument_type="INDEX",
        lot_size=25,
        tick_size=Decimal("0.05"),
        strike_interval=Decimal("50"),
        freeze_quantity=1800,
        weekly_expiry_day="TUESDAY",
        monthly_expiry_day="TUESDAY",
        category="INDEX",
    ),
    UnderlyingMaster(
        symbol="MIDCPNIFTY",
        display_name="NIFTY Midcap Select",
        exchange=ExchangeCode.NSEFO,
        instrument_type="INDEX",
        lot_size=50,
        tick_size=Decimal("0.05"),
        strike_interval=Decimal("25"),
        freeze_quantity=2800,
        weekly_expiry_day="MONDAY",
        monthly_expiry_day="MONDAY",
        category="INDEX",
    ),
    UnderlyingMaster(
        symbol="SENSEX",
        display_name="S&P BSE SENSEX",
        exchange=ExchangeCode.BSEFO,
        instrument_type="INDEX",
        lot_size=10,
        tick_size=Decimal("0.05"),
        strike_interval=Decimal("100"),
        freeze_quantity=500,
        weekly_expiry_day="FRIDAY",
        monthly_expiry_day="FRIDAY",
        category="INDEX",
    ),
]

PLACEHOLDER_CATEGORIES: dict[str, str] = {
    "STOCK": "Stock Options (placeholder)",
    "COMMODITY": "Commodity derivatives (placeholder)",
    "CURRENCY": "Currency derivatives (placeholder)",
}
