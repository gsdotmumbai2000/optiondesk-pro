"""Broker domain enumerations."""

from enum import Enum


class BrokerCode(str, Enum):
    """Supported broker identifiers."""

    BREEZE = "BREEZE"
    ZERODHA = "ZERODHA"
    DHAN = "DHAN"
    ANGEL_ONE = "ANGEL_ONE"
    UPSTOX = "UPSTOX"
    FYERS = "FYERS"
    SIMULATOR = "SIMULATOR"


class ConnectionState(str, Enum):
    """Broker connection lifecycle state."""

    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    AUTHENTICATING = "AUTHENTICATING"
    RECONNECTING = "RECONNECTING"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    RECONNECT_REQUIRED = "RECONNECT_REQUIRED"
    ERROR = "ERROR"


class BrokerConnectionStatus(str, Enum):
    """User-facing broker connection status labels."""

    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"
    AUTHENTICATION_FAILED = "Authentication Failed"
    EXPIRED = "Expired"
    RECONNECT_REQUIRED = "Reconnect Required"


class OrderSide(str, Enum):
    """Order action side."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Unified order type."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_MARKET = "STOP_LOSS_MARKET"
    BRACKET = "BRACKET"
    COVER = "COVER"


class ProductType(str, Enum):
    """Instrument product type."""

    CASH = "CASH"
    FUTURES = "FUTURES"
    OPTIONS = "OPTIONS"
    CURRENCY = "CURRENCY"
    COMMODITY = "COMMODITY"


class OrderValidity(str, Enum):
    """Order validity."""

    DAY = "DAY"
    IOC = "IOC"
    GTC = "GTC"


class OptionRight(str, Enum):
    """Option right."""

    CALL = "CALL"
    PUT = "PUT"


class HistoricalInterval(str, Enum):
    """Historical candle interval."""

    ONE_MINUTE = "1minute"
    FIVE_MINUTE = "5minute"
    FIFTEEN_MINUTE = "15minute"
    THIRTY_MINUTE = "30minute"
    ONE_HOUR = "1hour"
    ONE_DAY = "1day"


class QuoteSubscriptionMode(str, Enum):
    """Quote subscription mode."""

    LTP = "LTP"
    OHLC = "OHLC"
    DEPTH = "DEPTH"
    FULL = "FULL"
