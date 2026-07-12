"""Application services layer unit test skeletons."""

import pytest


@pytest.mark.skip(reason="skeleton")
def test_start_application_session() -> None:
    """Coordinator should create application session."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_trading_workspace_evaluate_strategy() -> None:
    """Trading workspace should delegate to strategy engine."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_trading_workspace_optimize_strategy() -> None:
    """Trading workspace should delegate to optimizer engine."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_portfolio_workspace_load_refresh() -> None:
    """Portfolio workspace should load and refresh via portfolio engine."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_portfolio_workspace_monitor() -> None:
    """Portfolio workspace should monitor via monitor engine."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_backtesting_workspace_run_pause_resume() -> None:
    """Backtesting workspace should manage run state."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_ai_workspace_generate_recommendation() -> None:
    """AI workspace should delegate to AI engine."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_command_dispatcher_open_strategy() -> None:
    """Command dispatcher should route open strategy command."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_query_dispatcher_get_portfolio() -> None:
    """Query dispatcher should return portfolio summary."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_workspace_coordinator_open_close() -> None:
    """Workspace coordinator should publish open/close events."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_navigation_service() -> None:
    """Navigation service should switch active workspace."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_session_recent_strategies() -> None:
    """Session manager should track recent strategies."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_workspace_cache() -> None:
    """Workspace cache should store recent data and reports."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_ui_never_calls_engines_directly() -> None:
    """Application layer should be sole engine interface."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_workspace_response_under_100ms() -> None:
    """Workspace operations should respond under 100 ms."""
    pass
