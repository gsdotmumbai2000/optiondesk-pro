"""Live analytics port for application workspaces."""

from typing import Protocol

from app.live.models.analytics import LiveAnalyticsSnapshot
from app.live.models.enums import RefreshMode
from app.live.models.option_chain import LiveOptionChain


class LiveAnalyticsPort(Protocol):
    """Read-only live analytics access for ViewModels."""

    def get_chain(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
    ) -> LiveOptionChain | None:
        """Return live option chain."""

    def get_analytics(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
    ) -> LiveAnalyticsSnapshot | None:
        """Return live analytics snapshot."""

    def request_refresh(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
    ) -> None:
        """Request manual analytics refresh."""

    def refresh_mode(self) -> RefreshMode:
        """Return current refresh mode."""
