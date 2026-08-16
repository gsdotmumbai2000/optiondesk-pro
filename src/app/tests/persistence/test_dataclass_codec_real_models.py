"""Proves the generic codec round-trips the actual production models it
will be used to persist -- Strategy, Portfolio, BacktestResult -- not just
the synthetic types in test_dataclass_codec.py.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.backtesting.models.enums import OrderSide, OrderType
from app.backtesting.models.metrics import PerformanceMetrics
from app.backtesting.models.result import BacktestResult
from app.backtesting.models.trades import (
    DrawdownCurve,
    DrawdownPoint,
    EquityCurve,
    EquityPoint,
    Trade as BacktestTrade,
    TradeLog,
)
from app.persistence.dataclass_codec import from_json, to_json
from app.portfolio.models.cash import CashAccount
from app.portfolio.models.enums import AssetClass, PositionStatus, TransactionType
from app.portfolio.models.portfolio import Portfolio
from app.portfolio.models.positions import Holding, Position
from app.portfolio.models.transactions import Trade, Transaction
from app.strategy.builders.strategy_builder import StrategyBuilder
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.strategy import Strategy


class TestStrategyRoundTrip:
    def test_strategy_with_multiple_legs_round_trips_exactly(self) -> None:
        legs = (
            StrategyLeg(
                leg_id="L1", kind=LegKind.CALL_BUY, quantity=1, premium=Decimal("100"),
                strike=Decimal("24500"), expiry=date(2026, 8, 18), underlying="NIFTY", exchange="NFO",
            ),
            StrategyLeg(
                leg_id="L2", kind=LegKind.CALL_SELL, quantity=1, premium=Decimal("50"),
                strike=Decimal("24600"), expiry=date(2026, 8, 18), underlying="NIFTY", exchange="NFO",
            ),
        )
        strategy = Strategy(metadata=StrategyBuilder(name="Bull Call Spread").build().metadata, legs=legs)

        restored = from_json(Strategy, to_json(strategy))

        assert restored == strategy
        assert restored.strategy_id == strategy.strategy_id
        assert len(restored.legs) == 2
        assert restored.legs[0].strike == Decimal("24500")
        assert restored.legs[1].expiry == date(2026, 8, 18)

    def test_leg_without_expiry_round_trips_none(self) -> None:
        leg = StrategyLeg(leg_id="L1", kind=LegKind.CALL_BUY, quantity=1, premium=Decimal("100"), expiry=None)
        strategy = Strategy(metadata=StrategyBuilder(name="Test").build().metadata, legs=(leg,))

        restored = from_json(Strategy, to_json(strategy))

        assert restored.legs[0].expiry is None


class TestPortfolioRoundTrip:
    def test_portfolio_with_nested_holdings_positions_and_transactions(self) -> None:
        portfolio = Portfolio(
            portfolio_id="P1", name="Main",
            cash_account=CashAccount(balance=Decimal("100000"), available=Decimal("80000"), reserved=Decimal("20000")),
            holdings=(
                Holding(
                    holding_id="H1", symbol="INFY", asset_class=AssetClass.STOCK, quantity=10,
                    average_price=Decimal("1500"), market_value=Decimal("15500"), unrealized_pnl=Decimal("500"),
                ),
            ),
            open_positions=(
                Position(
                    position_id="POS1", symbol="NIFTY24500CE", asset_class=AssetClass.OPTION, quantity=75,
                    entry_price=Decimal("100"), current_price=Decimal("120"), status=PositionStatus.OPEN,
                    opened_at=datetime(2026, 8, 16, 9, 15, tzinfo=timezone.utc),
                ),
            ),
            closed_positions=(),
            pending_orders=(),
            executed_orders=(
                Trade(
                    trade_id="T1", symbol="NIFTY24500CE", quantity=75, price=Decimal("100"), side="BUY",
                    executed_at=datetime(2026, 8, 16, 9, 15, tzinfo=timezone.utc),
                ),
            ),
            transactions=(
                Transaction(
                    transaction_id="TX1", transaction_type=TransactionType.BUY, symbol="NIFTY24500CE",
                    quantity=75, amount=Decimal("7500"), fees=Decimal("20"), taxes=Decimal("5"),
                    timestamp=datetime(2026, 8, 16, 9, 15, tzinfo=timezone.utc),
                ),
            ),
        )

        restored = from_json(Portfolio, to_json(portfolio))

        assert restored == portfolio
        assert restored.cash_account.available == Decimal("80000")
        assert restored.holdings[0].symbol == "INFY"
        assert restored.open_positions[0].status is PositionStatus.OPEN
        assert restored.transactions[0].transaction_type is TransactionType.BUY

    def test_empty_portfolio_round_trips(self) -> None:
        portfolio = Portfolio(
            portfolio_id="P2", name="Empty",
            cash_account=CashAccount(balance=Decimal("0"), available=Decimal("0"), reserved=Decimal("0")),
            holdings=(), open_positions=(), closed_positions=(),
            pending_orders=(), executed_orders=(), transactions=(),
        )

        restored = from_json(Portfolio, to_json(portfolio))

        assert restored == portfolio


class TestBacktestResultRoundTrip:
    def test_full_backtest_result_with_nested_curves_and_trade_log(self) -> None:
        result = BacktestResult(
            total_return=Decimal("0.15"), net_profit=Decimal("15000"), gross_profit=Decimal("20000"),
            gross_loss=Decimal("-5000"), maximum_drawdown=Decimal("-3000"), profit_factor=Decimal("4"),
            sharpe_ratio=Decimal("1.5"), sortino_ratio=Decimal("2.1"), calmar_ratio=Decimal("5"),
            expectancy=Decimal("150"), win_rate=Decimal("0.6"), loss_rate=Decimal("0.4"),
            average_win=Decimal("500"), average_loss=Decimal("-200"), largest_win=Decimal("2000"),
            largest_loss=Decimal("-800"), maximum_consecutive_wins=5, maximum_consecutive_losses=2,
            total_trades=100, winning_trades=60, losing_trades=40,
            average_holding_time=timedelta(hours=6, minutes=30),
            capital_utilization=Decimal("0.7"), margin_utilization=Decimal("0.5"),
            equity_curve=EquityCurve(points=(
                EquityPoint(timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), equity=Decimal("100000")),
                EquityPoint(timestamp=datetime(2026, 1, 2, tzinfo=timezone.utc), equity=Decimal("101500")),
            )),
            drawdown_curve=DrawdownCurve(points=(
                DrawdownPoint(timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), drawdown=Decimal("0")),
            )),
            trade_log=TradeLog(trades=(
                BacktestTrade(
                    trade_id="BT1", timestamp=datetime(2026, 1, 1, 10, tzinfo=timezone.utc), symbol="NIFTY",
                    side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=75, price=Decimal("24500"),
                    commission=Decimal("20"), slippage=Decimal("5"), pnl=Decimal("300"),
                    holding_time=timedelta(hours=2),
                ),
            )),
            performance_metrics=PerformanceMetrics(
                sharpe_ratio=Decimal("1.5"), sortino_ratio=Decimal("2.1"), calmar_ratio=Decimal("5"),
                profit_factor=Decimal("4"), expectancy=Decimal("150"), recovery_factor=Decimal("3"),
                return_on_capital=Decimal("0.15"), win_rate=Decimal("0.6"), loss_rate=Decimal("0.4"),
                average_win=Decimal("500"), average_loss=Decimal("-200"), largest_win=Decimal("2000"),
                largest_loss=Decimal("-800"), max_consecutive_wins=5, max_consecutive_losses=2,
                total_trades=100, winning_trades=60, losing_trades=40,
                average_holding_time=timedelta(hours=6, minutes=30),
                capital_utilization=Decimal("0.7"), margin_utilization=Decimal("0.5"),
            ),
            simulation_timestamp=datetime(2026, 8, 16, tzinfo=timezone.utc),
        )

        restored = from_json(BacktestResult, to_json(result))

        assert restored == result
        assert restored.average_holding_time == timedelta(hours=6, minutes=30)
        assert len(restored.equity_curve.points) == 2
        assert restored.trade_log.trades[0].side is OrderSide.BUY
        assert restored.performance_metrics.sharpe_ratio == Decimal("1.5")
