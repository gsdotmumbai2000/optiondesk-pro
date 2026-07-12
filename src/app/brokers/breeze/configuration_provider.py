"""Breeze configuration provider."""

from app.config.models.app_config import BreezeEnvironment, BrokerConfig
from app.security.credential_manager import CredentialManager


class BreezeConfigurationProvider:
    """Resolve Breeze settings and credentials from configuration."""

    def __init__(
        self,
        config: BrokerConfig,
        credential_manager: CredentialManager,
    ) -> None:
        """Initialize provider."""
        self._config = config
        self._credentials = credential_manager

    @property
    def account_name(self) -> str:
        """Return configured account name."""
        return self._config.account_name

    @property
    def user_id(self) -> str:
        """Return configured Breeze user id."""
        return self._config.user_id

    @property
    def environment(self) -> BreezeEnvironment:
        """Return Breeze API environment."""
        return self._config.environment

    @property
    def broker_code(self) -> str:
        """Return broker code."""
        return self._config.broker_code

    @property
    def config(self) -> BrokerConfig:
        """Return broker configuration."""
        return self._config

    def is_sandbox(self) -> bool:
        """Return whether sandbox environment is configured."""
        return self._config.environment == BreezeEnvironment.SANDBOX

    def get_api_key(self) -> str | None:
        """Return API key from secure storage."""
        return self._credentials.get_api_key(self._config.account_name)

    def get_api_secret(self) -> str | None:
        """Return API secret from secure storage."""
        return self._credentials.get_api_secret(self._config.account_name)

    def get_session_token(self) -> str | None:
        """Return session token from secure storage."""
        return self._credentials.get_session_token(self._config.account_name)

    def has_credentials(self) -> bool:
        """Return whether all required credentials are stored."""
        return all(
            (
                self.get_api_key(),
                self.get_api_secret(),
                self.get_session_token(),
            )
        )

    def store_session_token(self, session_token: str) -> None:
        """Persist session token securely."""
        self._credentials.store_session_token(self._config.account_name, session_token)

    def store_api_key(self, api_key: str) -> None:
        """Persist API key securely."""
        self._credentials.store_api_key(self._config.account_name, api_key)

    def store_api_secret(self, api_secret: str) -> None:
        """Persist API secret securely."""
        self._credentials.store_api_secret(self._config.account_name, api_secret)

    def clear_credentials(self) -> None:
        """Remove stored credentials for the account."""
        self._credentials.delete_credentials(self._config.account_name)
