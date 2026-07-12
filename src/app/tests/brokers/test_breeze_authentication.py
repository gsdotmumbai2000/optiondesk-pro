"""Broker authentication tests."""

from unittest.mock import MagicMock

import pytest

from app.brokers.breeze.authentication import BreezeAuthentication
from app.brokers.shared.exceptions import BrokerAuthenticationException
from app.security.credential_manager import CredentialManager


def test_authenticate_success() -> None:
    """Authentication should succeed with valid credentials."""
    client = MagicMock()
    client.generate_session.return_value = {"Success": {}}
    client.get_customer_details.return_value = {"Success": {"idirect_userid": "1"}}
    manager = CredentialManager()
    manager.store_api_key("Default", "key")
    manager.store_api_secret("Default", "secret")
    manager.store_session_token("Default", "token")
    auth = BreezeAuthentication(client, manager, "Default")
    auth.authenticate()
    assert auth.session_token == "token"
    assert auth.validate_session() is True


def test_authenticate_missing_credentials() -> None:
    """Authentication should fail without credentials."""
    auth = BreezeAuthentication(MagicMock(), CredentialManager(), "MissingAccount")
    with pytest.raises(BrokerAuthenticationException):
        auth.authenticate()
