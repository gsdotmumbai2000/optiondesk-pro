"""Portfolio domain enumerations."""

from enum import Enum


class PortfolioModelVersion(str, Enum):
    """Portfolio engine schema version."""

    V1 = "portfolio-engine-v1"


class AssetClass(str, Enum):
    """Holding asset classes."""

    STOCK = "STOCK"
    OPTION = "OPTION"
    FUTURE = "FUTURE"
    CASH = "CASH"
    ETF = "ETF"
    CURRENCY = "CURRENCY"


class PositionStatus(str, Enum):
    """Position lifecycle status."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PARTIAL = "PARTIAL"


class TransactionType(str, Enum):
    """Transaction types."""

    BUY = "BUY"
    SELL = "SELL"
    FEE = "FEE"
    TAX = "TAX"
    DIVIDEND = "DIVIDEND"
    CORPORATE_ACTION = "CORPORATE_ACTION"


class OrderStatus(str, Enum):
    """Order status."""

    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
