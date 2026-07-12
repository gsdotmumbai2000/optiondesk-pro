"""Market Master domain enums."""

from enum import Enum


class InstrumentType(str, Enum):
    """Supported instrument types."""

    INDEX = "INDEX"
    STOCK = "STOCK"
    FUTURE = "FUTURE"
    OPTION = "OPTION"
    COMMODITY = "COMMODITY"
    CURRENCY = "CURRENCY"
    ETF = "ETF"


class ExchangeCode(str, Enum):
    """Supported exchange identifiers."""

    NSE = "NSE"
    BSE = "BSE"
    MCX = "MCX"
    NSEFO = "NSEFO"
    BSEFO = "BSEFO"


class ExpiryType(str, Enum):
    """Expiry classification."""

    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"


class SessionType(str, Enum):
    """Trading session classification."""

    REGULAR = "REGULAR"
    PRE_OPEN = "PRE_OPEN"
    POST_CLOSE = "POST_CLOSE"
    BLOCK_DEAL = "BLOCK_DEAL"
    AUCTION = "AUCTION"
    MUHURAT = "MUHURAT"
    HOLIDAY = "HOLIDAY"


class Weekday(str, Enum):
    """Weekday names for expiry rules."""

    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"
