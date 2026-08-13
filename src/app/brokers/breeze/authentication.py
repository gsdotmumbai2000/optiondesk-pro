"""Breeze authentication."""

from app.brokers.breeze.client_port import BreezeClientPort
from app.brokers.shared.exceptions import BrokerAuthenticationException
from app.logging.logging_manager import get_logger
from app.security.credential_manager import CredentialManager

logger = get_logger(__name__)


class BreezeAuthentication:
    """Handle Breeze API authentication."""

    def __init__(
        self,
        client: BreezeClientPort,
        credential_manager: CredentialManager,
        account_name: str,
    ) -> None:
        """Initialize authentication helper."""
        self._client = client
        self._credential_manager = credential_manager
        self._account_name = account_name
        self._session_token = ""

    @property
    def session_token(self) -> str:
        """Return active session token."""
        return self._session_token

    def authenticate(self) -> None:
        """Authenticate using stored credentials."""
        api_key = self._credential_manager.get_api_key(self._account_name)
        api_secret = self._credential_manager.get_api_secret(self._account_name)
        session_token = self._credential_manager.get_session_token(self._account_name)
        if not api_key or not api_secret or not session_token:
            raise BrokerAuthenticationException(
                "Missing Breeze credentials in CredentialManager"
            )
        response = self._client.generate_session(api_secret, session_token)
        if isinstance(response, dict) and response.get("Error"):
            raise BrokerAuthenticationException(str(response["Error"]))
        self._session_token = session_token

    def validate_session(self) -> bool:
        """Validate current session with customer details API."""
        if not self._session_token:
            return False
        logger.debug("BEFORE Breeze get_customer_details(...) [session validation]")
        response = self._client.get_customer_details(api_session=self._session_token)
        logger.debug("AFTER Breeze get_customer_details(...) [session validation]")
        if response.get("Error"):
            return False
        return "Success" in response

    def refresh_session(self) -> None:
        """Re-authenticate using stored session token."""
        self.authenticate()

    def logout(self) -> None:
        """Clear in-memory session token."""
        self._session_token = ""
