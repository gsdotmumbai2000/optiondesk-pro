"""Paper trading application service: one virtual account per account_id,
created lazily on first use."""

from decimal import Decimal
from threading import RLock

from app.backtesting.models.config import ExecutionConfig
from app.paper_trading.engine.paper_trading_account import PaperTradingAccount
from app.paper_trading.models.account import PaperAccountSnapshot, PaperTrade
from app.paper_trading.models.request import PaperOrderRequest

_DEFAULT_INITIAL_CAPITAL = Decimal("1000000")


class PaperTradingService:
    """Manage per-account paper trading state."""

    def __init__(
        self,
        default_initial_capital: Decimal = _DEFAULT_INITIAL_CAPITAL,
        execution_config: ExecutionConfig | None = None,
    ) -> None:
        self._default_initial_capital = default_initial_capital
        self._execution_config = execution_config
        self._lock = RLock()
        self._accounts: dict[str, PaperTradingAccount] = {}

    def submit_order(self, account_id: str, request: PaperOrderRequest) -> PaperTrade:
        """Simulate a fill for `request` against `account_id`'s account
        (created with the default starting capital if this is its first
        order)."""
        return self._account(account_id).submit_order(request)

    def snapshot(self, account_id: str) -> PaperAccountSnapshot:
        """Return `account_id`'s current state."""
        return self._account(account_id).snapshot()

    def trade_history(self, account_id: str) -> tuple[PaperTrade, ...]:
        """Return `account_id`'s trade history, oldest first."""
        return self._account(account_id).trade_history()

    def reset(self, account_id: str, initial_capital: Decimal | None = None) -> PaperAccountSnapshot:
        """Discard `account_id`'s state and start a fresh account."""
        capital = initial_capital if initial_capital is not None else self._default_initial_capital
        with self._lock:
            account = PaperTradingAccount(account_id, capital, self._execution_config)
            self._accounts[account_id] = account
        return account.snapshot()

    def _account(self, account_id: str) -> PaperTradingAccount:
        with self._lock:
            account = self._accounts.get(account_id)
            if account is None:
                account = PaperTradingAccount(account_id, self._default_initial_capital, self._execution_config)
                self._accounts[account_id] = account
            return account
