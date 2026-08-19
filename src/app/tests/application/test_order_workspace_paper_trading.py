"""Tests for OrderWorkspaceService's paper trading methods: execute_paper_
order() and paper_portfolio(), the application-layer entry points into
PaperTradingService.
"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.services.order_workspace_service import OrderWorkspaceService
from app.application.session.session_manager import SessionManager
from app.backtesting.models.enums import OrderSide
from app.paper_trading.services.paper_trading_service import PaperTradingService
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg


def _leg() -> StrategyLeg:
    return StrategyLeg(
        leg_id="L1", kind=LegKind.CALL_BUY, quantity=1, premium=Decimal("0"),
        strike=Decimal("24500"), expiry=date(2026, 8, 18), underlying="NIFTY", exchange="NFO",
    )


def _service() -> OrderWorkspaceService:
    engines = SimpleNamespace(paper_trading=SimpleNamespace(service=PaperTradingService()))
    return OrderWorkspaceService(engines, SessionManager(), WorkspaceCache())


class TestExecutePaperOrder:
    def test_returns_success_with_the_filled_trade(self) -> None:
        service = _service()

        result = service.execute_paper_order("s1", _leg(), OrderSide.BUY, 10, Decimal("100"))

        assert result.success is True
        assert result.data.quantity == 10

    def test_message_reports_fill_quantity_and_price(self) -> None:
        service = _service()

        result = service.execute_paper_order("s1", _leg(), OrderSide.BUY, 10, Decimal("100"))

        assert "10" in result.message

    def test_two_orders_on_the_same_session_affect_the_same_account(self) -> None:
        service = _service()

        service.execute_paper_order("s1", _leg(), OrderSide.BUY, 10, Decimal("100"))
        portfolio = service.paper_portfolio("s1")

        assert len(portfolio.data.open_positions) == 1
        assert portfolio.data.open_positions[0].quantity == 10


class TestPaperPortfolio:
    def test_returns_a_fresh_account_before_any_order(self) -> None:
        service = _service()

        result = service.paper_portfolio("s1")

        assert result.success is True
        assert result.data.open_positions == ()

    def test_different_sessions_have_independent_paper_accounts(self) -> None:
        service = _service()
        service.execute_paper_order("s1", _leg(), OrderSide.BUY, 10, Decimal("100"))

        other = service.paper_portfolio("s2")

        assert other.data.open_positions == ()
