"""Credential management using Windows DPAPI."""

import sys
from typing import Final

from app.exceptions.application_exception import ApplicationException
from app.logging.logging_manager import get_logger
from app.utils.constants import (CREDENTIAL_API_KEY, CREDENTIAL_API_SECRET,
                                 CREDENTIAL_SERVICE_NAME,
                                 CREDENTIAL_SESSION_TOKEN)

logger = get_logger(__name__)


class CredentialManager:
    """Secure credential storage. Secrets are never stored in SQLite."""

    def __init__(self, service_name: str = CREDENTIAL_SERVICE_NAME) -> None:
        """Initialize the credential manager."""
        self._service_name = service_name
        self._memory_store: dict[str, str] = {}

    def store_api_key(self, account_id: str, api_key: str) -> None:
        """Store an API key securely."""
        self._store(self._key(CREDENTIAL_API_KEY, account_id), api_key)

    def store_api_secret(self, account_id: str, api_secret: str) -> None:
        """Store an API secret securely."""
        self._store(self._key(CREDENTIAL_API_SECRET, account_id), api_secret)

    def store_session_token(self, account_id: str, session_token: str) -> None:
        """Store a session token securely."""
        self._store(self._key(CREDENTIAL_SESSION_TOKEN, account_id), session_token)

    def get_api_key(self, account_id: str) -> str | None:
        """Retrieve an API key."""
        return self._retrieve(self._key(CREDENTIAL_API_KEY, account_id))

    def get_api_secret(self, account_id: str) -> str | None:
        """Retrieve an API secret."""
        return self._retrieve(self._key(CREDENTIAL_API_SECRET, account_id))

    def get_session_token(self, account_id: str) -> str | None:
        """Retrieve a session token."""
        return self._retrieve(self._key(CREDENTIAL_SESSION_TOKEN, account_id))

    def delete_credentials(self, account_id: str) -> None:
        """Delete all credentials for an account."""
        for suffix in (
            CREDENTIAL_API_KEY,
            CREDENTIAL_API_SECRET,
            CREDENTIAL_SESSION_TOKEN,
        ):
            self._delete(self._key(suffix, account_id))

    def _store(self, key: str, value: str) -> None:
        """Store a credential value."""
        if sys.platform == "win32":
            self._store_dpapi(key, value)
            return
        self._memory_store[key] = value
        logger.warning("Using in-memory credential store (non-Windows platform)")

    def _retrieve(self, key: str) -> str | None:
        """Retrieve a credential value."""
        if sys.platform == "win32":
            return self._retrieve_dpapi(key)
        return self._memory_store.get(key)

    def _delete(self, key: str) -> None:
        """Delete a credential value."""
        if sys.platform == "win32":
            self._delete_credential_manager(key)
            return
        self._memory_store.pop(key, None)

    def _store_dpapi(self, key: str, value: str) -> None:
        """Store using Windows Credential Manager."""
        try:
            import win32cred
        except ImportError as error:
            raise ApplicationException("pywin32 is required on Windows") from error

        target: Final = self._credential_target(key)
        win32cred.CredWrite(
            {
                "Type": win32cred.CRED_TYPE_GENERIC,
                "TargetName": target,
                "UserName": key,
                "CredentialBlob": value,
                "Persist": win32cred.CRED_PERSIST_LOCAL_MACHINE,
            },
            0,
        )

    def _retrieve_dpapi(self, key: str) -> str | None:
        """Retrieve from Windows Credential Manager."""
        try:
            import win32cred
        except ImportError:
            return None

        target = self._credential_target(key)
        try:
            credential = win32cred.CredRead(target, win32cred.CRED_TYPE_GENERIC)
        except Exception:
            return None
        blob = credential["CredentialBlob"]
        return blob.decode("utf-16-le") if isinstance(blob, bytes) else str(blob)

    def _delete_credential_manager(self, key: str) -> None:
        """Delete from Windows Credential Manager."""
        try:
            import win32cred
        except ImportError:
            return
        target = self._credential_target(key)
        try:
            win32cred.CredDelete(target, win32cred.CRED_TYPE_GENERIC)
        except Exception:
            logger.debug("Credential not found for deletion: {key}", key=key)

    def _credential_target(self, key: str) -> str:
        """Build a credential manager target name."""
        return f"{self._service_name}/{key}"

    @staticmethod
    def _key(suffix: str, account_id: str) -> str:
        """Build an internal credential key."""
        return f"{suffix}:{account_id}"
