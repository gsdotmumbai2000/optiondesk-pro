"""Tests for PaperTradingService: per-account lazy creation, isolation
between accounts, and reset.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

from app.backtesting.models.enums import OrderSide
from app.paper_trading.models.request import PaperOrderRequest
from app.paper_trading.services.paper_trading_service import PaperTradingService
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg

_NOW = datetime(2026, 8, 16, 10, 0, tzinfo=timezone.utc)


def _leg() -> StrategyLeg:
    return StrategyLeg(
        leg_id="L1", kind=LegKind.CALL_BUY, quantity=1, premium=Decimal("0"),
        strike=Decimal("24500"), expiry=date(2026, 8, 18), underlying="NIFTY", exchange="NFO",
    )


def _order(quantity: int = 10, price: str = "100") -> PaperOrderRequest:
    return PaperOrderRequest(leg=_leg(), side=OrderSide.BUY, quantity=quantity, reference_price=Decimal(price), timestamp=_NOW)


class TestLazyAccountCreation:
    def test_first_snapshot_creates_account_with_default_capital(self) -> None:
        service = PaperTradingService(default_initial_capital=Decimal("250000"))

        snapshot = service.snapshot("session-1")

        assert snapshot.account_id == "session-1"
        assert snapshot.cash_balance == Decimal("250000")

    def test_empty_trade_history_before_any_order(self) -> None:
        service = PaperTradingService()

        assert service.trade_history("session-1") == ()


class TestAccountIsolation:
    def test_orders_on_one_account_do_not_affect_another(self) -> None:
        service = PaperTradingService(default_initial_capital=Decimal("100000"))

        service.submit_order("session-1", _order())

        assert service.snapshot("session-1").cash_balance != Decimal("100000")
        assert service.snapshot("session-2").cash_balance == Decimal("100000")

    def test_trade_history_is_per_account(self) -> None:
        service = PaperTradingService()

        service.submit_order("session-1", _order())

        assert len(service.trade_history("session-1")) == 1
        assert len(service.trade_history("session-2")) == 0


class TestReset:
    def test_reset_restores_default_capital(self) -> None:
        service = PaperTradingService(default_initial_capital=Decimal("100000"))
        service.submit_order("session-1", _order())
        assert service.snapshot("session-1").open_positions != ()

        snapshot = service.reset("session-1")

        assert snapshot.cash_balance == Decimal("100000")
        assert snapshot.open_positions == ()
        assert service.trade_history("session-1") == ()

    def test_reset_with_explicit_capital_overrides_default(self) -> None:
        service = PaperTradingService(default_initial_capital=Decimal("100000"))

        snapshot = service.reset("session-1", Decimal("500000"))

        assert snapshot.cash_balance == Decimal("500000")
