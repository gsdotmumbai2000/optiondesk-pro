"""Temporary market data pipeline diagnostic configuration."""

# Set to False to disable all market data debug logging.
MARKET_DATA_DEBUG: bool = True


def market_data_debug_enabled() -> bool:
    """Return whether market data diagnostic logging is active."""
    return MARKET_DATA_DEBUG
