"""Unit test skeletons for live validation."""

import pytest


@pytest.mark.skip(reason="Skeleton only")
def test_tick_validator_rejects_future_timestamp() -> None:
    """TickValidator should reject ticks from the future."""
    assert True


@pytest.mark.skip(reason="Skeleton only")
def test_chain_validator_requires_underlying() -> None:
    """ChainValidator should reject empty underlying."""
    assert True


@pytest.mark.skip(reason="Skeleton only")
def test_freshness_validator_detects_stale_snapshot() -> None:
    """FreshnessValidator should reject stale analytics."""
    assert True
