"""Breeze configuration provider tests."""

import pytest

from app.brokers.breeze.configuration_provider import BreezeConfigurationProvider
from app.config.models.app_config import BrokerConfig
from app.security.credential_manager import CredentialManager


@pytest.mark.skip("Skeleton — implement configuration provider tests")
def test_has_credentials_when_all_stored() -> None:
    """Provider should report credentials present when all values stored."""
    config = BrokerConfig()
    manager = CredentialManager()
    provider = BreezeConfigurationProvider(config, manager)
    assert provider.has_credentials() is False


@pytest.mark.skip("Skeleton — implement environment resolution")
def test_is_sandbox() -> None:
    """Provider should detect sandbox environment."""
    pass
