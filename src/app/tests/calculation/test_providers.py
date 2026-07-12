"""Calculation provider unit test skeletons."""

import pytest


@pytest.mark.skip(reason="skeleton")
def test_interest_rate_provider_defaults() -> None:
    """InterestRateProvider should return normalized defaults."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_dividend_provider_defaults() -> None:
    """DividendProvider should return normalized dividend yield."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_volatility_provider_from_option_chain() -> None:
    """VolatilityProvider should prefer ATM implied volatility."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_expiry_provider_parses_formats() -> None:
    """ExpiryProvider should parse supported expiry formats."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_market_status_provider_session() -> None:
    """MarketStatusProvider should build market session snapshots."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_underlying_provider_resolve() -> None:
    """UnderlyingProvider should normalize underlying metadata."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_market_data_port_adapter_delegates() -> None:
    """Market data adapter should delegate to query service."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_instrument_port_adapter_delegates() -> None:
    """Instrument adapter should delegate to instrument service."""
    pass
