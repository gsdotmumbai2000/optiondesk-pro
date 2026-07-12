"""Persist Breeze session metadata (tokens remain in CredentialManager)."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.config.models.app_config import BreezeEnvironment
from app.logging.logging_manager import get_logger
from app.utils.file_helper import FileHelper

logger = get_logger(__name__)


@dataclass(slots=True)
class BreezeSessionSnapshot:
    """Non-secret session metadata for restore after restart."""

    account_name: str
    user_id: str
    environment: str
    session_started: str
    is_valid: bool = True


class BreezeSessionStore:
    """File-backed session metadata store."""

    def __init__(self, data_directory: Path) -> None:
        """Initialize session store."""
        self._path = data_directory / "broker" / "breeze_session.json"
        FileHelper.ensure_directory(self._path.parent)

    def save(self, snapshot: BreezeSessionSnapshot) -> None:
        """Persist session metadata."""
        payload = asdict(snapshot)
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        logger.info(
            "Breeze session metadata saved for account {account}",
            account=snapshot.account_name,
        )

    def load(self) -> BreezeSessionSnapshot | None:
        """Load session metadata if present."""
        if not self._path.exists():
            return None
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
            return BreezeSessionSnapshot(**payload)
        except (json.JSONDecodeError, TypeError) as error:
            logger.warning("Invalid Breeze session metadata: {error}", error=error)
            return None

    def clear(self) -> None:
        """Remove persisted session metadata."""
        if self._path.exists():
            self._path.unlink()
            logger.info("Breeze session metadata cleared")

    @staticmethod
    def build_snapshot(
        account_name: str,
        user_id: str,
        environment: BreezeEnvironment,
        *,
        is_valid: bool = True,
    ) -> BreezeSessionSnapshot:
        """Build a new session snapshot."""
        started = datetime.now(timezone.utc).isoformat()
        return BreezeSessionSnapshot(
            account_name=account_name,
            user_id=user_id,
            environment=environment.value,
            session_started=started,
            is_valid=is_valid,
        )
