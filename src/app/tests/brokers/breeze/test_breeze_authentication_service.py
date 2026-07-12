"""Breeze authentication service tests."""

import pytest


@pytest.mark.skip("Skeleton — implement login success flow")
def test_login_publishes_success_event() -> None:
    """Login should publish AuthenticationSucceededEvent on success."""
    pass


@pytest.mark.skip("Skeleton — implement login failure flow")
def test_login_publishes_failure_event() -> None:
    """Login should publish AuthenticationFailedEvent on invalid credentials."""
    pass


@pytest.mark.skip("Skeleton — implement reconnect with backoff")
def test_reconnect_retries_on_timeout() -> None:
    """Reconnect should retry with exponential backoff on timeout."""
    pass


@pytest.mark.skip("Skeleton — implement session restore")
def test_restore_session_after_restart() -> None:
    """Restore should validate persisted session metadata and token."""
    pass
