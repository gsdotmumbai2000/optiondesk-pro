"""Order workspace service (no broker logic)."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult, WorkspaceView
from app.application.registry.engine_registry import EngineRegistry
from app.application.session.session_manager import SessionManager


@dataclass(frozen=True, slots=True)
class OrderIntent:
    """Order intent model (framework, no broker execution)."""

    symbol: str
    quantity: int
    side: str
    price: Decimal
    portfolio_id: str


class OrderWorkspaceService:
    """Order management workspace API (orchestration only)."""

    def __init__(
        self,
        engines: EngineRegistry,
        sessions: SessionManager,
        cache: WorkspaceCache,
    ) -> None:
        """Initialize service."""
        self._engines = engines
        self._sessions = sessions
        self._cache = cache
        self._pending: dict[str, tuple[OrderIntent, ...]] = {}

    def submit_intent(
        self,
        session_id: str,
        intent: OrderIntent,
    ) -> WorkspaceOperationResult:
        """Queue order intent (no broker execution)."""
        pending = self._pending.get(session_id, ()) + (intent,)
        self._pending[session_id] = pending
        self._cache.put_data(f"{session_id}:orders", pending)
        return WorkspaceOperationResult(
            True,
            WorkspaceType.ORDER,
            f"Order intent queued for {intent.symbol}",
            intent,
        )

    def pending_orders(self, session_id: str) -> tuple[OrderIntent, ...]:
        """Return pending order intents."""
        return self._pending.get(session_id, ())

    def open_positions(self, portfolio_id: str) -> WorkspaceOperationResult:
        """Return open positions from portfolio engine."""
        portfolio = self._engines.portfolio.repository.get(portfolio_id)
        if portfolio is None:
            return WorkspaceOperationResult(
                False,
                WorkspaceType.ORDER,
                "Portfolio not found",
            )
        return WorkspaceOperationResult(
            True,
            WorkspaceType.ORDER,
            f"{len(portfolio.open_positions)} open positions",
            portfolio.open_positions,
        )

    def view(self, session_id: str) -> WorkspaceView:
        """Return order workspace view."""
        count = len(self._pending.get(session_id, ()))
        return WorkspaceView(
            workspace=WorkspaceType.ORDER,
            title="Order Workspace",
            summary=f"{count} pending intents",
            entity_id="",
            updated_at=datetime.now(timezone.utc),
        )
