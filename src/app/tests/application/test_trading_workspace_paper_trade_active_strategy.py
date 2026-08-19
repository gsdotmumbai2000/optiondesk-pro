"""Tests for TradingWorkspaceService.paper_trade_active_strategy(): submits
every leg of whatever strategy is currently loaded into this session's
Trading workspace as a paper order, using each leg's own recorded premium
as the reference price -- no live chain subscription required.
"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.services.trading_workspace_service import TradingWorkspaceService
from app.application.session.session_manager import SessionManager
from app.backtesting.models.enums import OrderSide
from app.strategy.builders.strategy_builder import StrategyBuilder
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.strategy import Strategy


class _RecordingPaperTradingService:
    def __init__(self) -> None:
        self.received_orders: list = []
        self.snapshot_calls: list[str] = []
        self._snapshot = SimpleNamespace(
            equity=Decimal("999972.2"), cash_balance=Decimal("1019462.45"),
            open_positions=(SimpleNamespace(),), realized_pnl=Decimal("0"),
        )

    def submit_order(self, account_id: str, request):
        self.received_orders.append((account_id, request))
        return SimpleNamespace(trade_id="T1")

    def snapshot(self, account_id: str):
        self.snapshot_calls.append(account_id)
        return self._snapshot


def _leg(**overrides) -> StrategyLeg:
    defaults = dict(
        leg_id="L1", kind=LegKind.CALL_SELL, quantity=195, premium=Decimal("100"),
        strike=Decimal("25000"), underlying="NIFTY", exchange="NFO",
        expiry=date(2026, 8, 18),
    )
    defaults.update(overrides)
    return StrategyLeg(**defaults)


def _strategy(legs: tuple[StrategyLeg, ...]) -> Strategy:
    return Strategy(metadata=StrategyBuilder(name="Test").build().metadata, legs=legs)


def _service_with_active_strategy(
    strategy: Strategy | None,
) -> tuple[TradingWorkspaceService, str, _RecordingPaperTradingService]:
    sessions = SessionManager()
    cache = WorkspaceCache()
    session = sessions.create(WorkspaceType.TRADING)
    if strategy is not None:
        cache.put_strategy(strategy.strategy_id, strategy)
        sessions.set_active_workspace(session.session_id, WorkspaceType.TRADING, strategy.strategy_id)
    paper_service = _RecordingPaperTradingService()
    engines = SimpleNamespace(paper_trading=SimpleNamespace(service=paper_service))
    service = TradingWorkspaceService(engines=engines, sessions=sessions, cache=cache)
    return service, session.session_id, paper_service


class TestPaperTradeActiveStrategySuccess:
    def test_returns_success_with_account_snapshot(self) -> None:
        strategy = _strategy((_leg(),))
        service, session_id, paper_service = _service_with_active_strategy(strategy)

        result = service.paper_trade_active_strategy(session_id)

        assert result.success is True
        assert result.data is paper_service._snapshot  # noqa: SLF001

    def test_submits_one_order_per_leg(self) -> None:
        legs = (_leg(leg_id="L1", strike=Decimal("25000")), _leg(leg_id="L2", strike=Decimal("24700"), kind=LegKind.CALL_BUY))
        strategy = _strategy(legs)
        service, session_id, paper_service = _service_with_active_strategy(strategy)

        service.paper_trade_active_strategy(session_id)

        assert len(paper_service.received_orders) == 2

    def test_sell_leg_maps_to_sell_side(self) -> None:
        strategy = _strategy((_leg(kind=LegKind.CALL_SELL),))
        service, session_id, paper_service = _service_with_active_strategy(strategy)

        service.paper_trade_active_strategy(session_id)

        _, request = paper_service.received_orders[0]
        assert request.side == OrderSide.SELL

    def test_buy_leg_maps_to_buy_side(self) -> None:
        strategy = _strategy((_leg(kind=LegKind.PUT_BUY),))
        service, session_id, paper_service = _service_with_active_strategy(strategy)

        service.paper_trade_active_strategy(session_id)

        _, request = paper_service.received_orders[0]
        assert request.side == OrderSide.BUY

    def test_reference_price_is_the_legs_own_premium(self) -> None:
        strategy = _strategy((_leg(premium=Decimal("123.45")),))
        service, session_id, paper_service = _service_with_active_strategy(strategy)

        service.paper_trade_active_strategy(session_id)

        _, request = paper_service.received_orders[0]
        assert request.reference_price == Decimal("123.45")

    def test_quantity_is_the_legs_absolute_magnitude(self) -> None:
        strategy = _strategy((_leg(quantity=-195),))  # a signed quantity, e.g. from to_payoff_legs
        service, session_id, paper_service = _service_with_active_strategy(strategy)

        service.paper_trade_active_strategy(session_id)

        _, request = paper_service.received_orders[0]
        assert request.quantity == 195

    def test_orders_submitted_against_this_session_id_as_account_id(self) -> None:
        strategy = _strategy((_leg(),))
        service, session_id, paper_service = _service_with_active_strategy(strategy)

        service.paper_trade_active_strategy(session_id)

        account_id, _ = paper_service.received_orders[0]
        assert account_id == session_id
        assert paper_service.snapshot_calls == [session_id]

    def test_message_reports_leg_count_and_equity(self) -> None:
        strategy = _strategy((_leg(),))
        service, session_id, _ = _service_with_active_strategy(strategy)

        result = service.paper_trade_active_strategy(session_id)

        assert "1 leg" in result.message
        assert "999972.2" in result.message


class TestPaperTradeActiveStrategyUnavailableFallsBackGracefully:
    def test_no_active_strategy_returns_failure_without_crashing(self) -> None:
        service, session_id, paper_service = _service_with_active_strategy(None)

        result = service.paper_trade_active_strategy(session_id)

        assert result.success is False
        assert result.message == "No active strategy to paper trade"
        assert paper_service.received_orders == []

    def test_strategy_with_no_legs_returns_failure(self) -> None:
        strategy = _strategy(())
        service, session_id, paper_service = _service_with_active_strategy(strategy)

        result = service.paper_trade_active_strategy(session_id)

        assert result.success is False
        assert result.message == "Strategy has no legs to paper trade"
        assert paper_service.received_orders == []
