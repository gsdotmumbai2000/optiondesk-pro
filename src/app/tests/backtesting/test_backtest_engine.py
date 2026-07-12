"""Backtesting engine unit test skeletons."""

import pytest


@pytest.mark.skip(reason="skeleton")
def test_replay_engine_step_forward() -> None:
    """Replay engine should step through historical bars."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_replay_pause_resume() -> None:
    """Replay engine should support pause and resume."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_execution_simulator_slippage() -> None:
    """Execution simulator should apply slippage and fees."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_execution_partial_fill() -> None:
    """Execution simulator should support partial fills."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_portfolio_tracker_pnl() -> None:
    """Portfolio tracker should track cash and PnL."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_performance_analytics_sharpe() -> None:
    """Analytics should compute Sharpe ratio from equity curve."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_backtest_engine_orchestration() -> None:
    """Backtest engine should orchestrate replay and execution."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_backtest_uses_engine_outputs() -> None:
    """Backtest should consume margin and PnL from strategy context."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_backtest_validator_rejects_empty_bars() -> None:
    """Validator should reject empty historical data."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_backtest_service_caches_results() -> None:
    """Backtest service should cache latest results."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_backtest_events_published() -> None:
    """Service should publish replay and completion events."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_hundred_k_bar_replay_performance() -> None:
    """100,000 bars should replay in under 5 seconds."""
    pass
