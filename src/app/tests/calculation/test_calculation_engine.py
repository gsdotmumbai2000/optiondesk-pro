"""Calculation engine unit test skeletons."""

import pytest


@pytest.mark.skip(reason="skeleton")
def test_calculation_context_is_immutable() -> None:
    """CalculationContext should reject mutation."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_context_factory_builds_valid_context() -> None:
    """Factory should assemble and validate a context."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_context_factory_publishes_created_event() -> None:
    """Factory should publish CalculationContextCreatedEvent."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_context_factory_publishes_invalid_event() -> None:
    """Factory should publish CalculationContextInvalidEvent on failure."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_context_validator_rejects_invalid_spot() -> None:
    """Validator should reject non-positive spot prices."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_context_validator_rejects_expired_contract() -> None:
    """Validator should reject expiry before trade date."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_context_cache_latest_and_previous() -> None:
    """Cache should retain latest and previous contexts."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_context_cache_compare_detects_changes() -> None:
    """Cache compare should detect material field changes."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_context_cache_expire_removes_entries() -> None:
    """Cache expire should remove cached contexts."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_context_serializer_json_round_trip() -> None:
    """Serializer should round-trip contexts via JSON."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_context_serializer_binary_round_trip() -> None:
    """Serializer should round-trip contexts via binary encoding."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_calculation_engine_create_context() -> None:
    """Engine should delegate context creation to service."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_calculation_provider_wires_dependencies() -> None:
    """Bootstrap provider should wire engine dependencies."""
    pass
