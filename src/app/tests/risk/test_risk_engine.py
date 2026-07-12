"""Risk engine unit test skeletons."""

import pytest


@pytest.mark.skip(reason="skeleton")
def test_greeks_aggregation() -> None:
    """Aggregator should compute net portfolio Greeks."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_parametric_var() -> None:
    """Parametric VaR should return value at 95% and 99%."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_historical_var() -> None:
    """Historical VaR should use realized volatility."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_variance_covariance_var() -> None:
    """Variance-covariance VaR should compute daily VaR."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_expected_shortfall() -> None:
    """CVaR calculator should return tail loss."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_stress_price_shocks() -> None:
    """Stress runner should handle ±1% to ±20% price shocks."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_stress_iv_and_time() -> None:
    """Stress runner should handle IV and time decay shocks."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_risk_limit_warnings() -> None:
    """Limit checker should generate warnings when exceeded."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_portfolio_exposure() -> None:
    """Exposure calculator should break down by underlying and expiry."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_scenario_ranking() -> None:
    """Scenario engine should rank scenarios by loss severity."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_risk_service_caches_results() -> None:
    """Risk service should cache latest results."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_risk_events_published() -> None:
    """Service should publish RiskCalculated and limit events."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_hundred_position_performance() -> None:
    """100-position risk analysis should complete in under 10 ms."""
    pass
