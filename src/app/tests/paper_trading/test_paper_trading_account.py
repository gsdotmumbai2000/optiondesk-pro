"""Tests for PaperTradingAccount: position netting (open/add/partial-close/
full-close/reversal) and cash accounting around real fills from the
backtesting engine's ExecutionSimulator.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

from app.backtesting.models.config import ExecutionConfig
from app.backtesting.models.enums import OrderSide
from app.paper_trading.engine.paper_trading_account import PaperTradingAccount
from app.paper_trading.models.request import PaperOrderRequest
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg

_NOW = datetime(2026, 8, 16, 10, 0, tzinfo=timezone.utc)
_EXPIRY = date(2026, 8, 18)

# No slippage/commission, so fills land exactly on the reference price --
# isolates position-netting/cash logic from ExecutionSimulator's own math
# (that's covered separately by backtesting's own tests).
_NO_COST_CONFIG = ExecutionConfig(
    slippage_pct=Decimal("0"), commission_per_trade=Decimal("0"),
    brokerage_pct=Decimal("0"), exchange_charges_pct=Decimal("0"),
    partial_fill_enabled=False,
)


def _leg(kind: LegKind, strike: str = "24500", underlying: str = "NIFTY") -> StrategyLeg:
    return StrategyLeg(
        leg_id="L1", kind=kind, quantity=1, premium=Decimal("0"),
        strike=Decimal(strike), expiry=_EXPIRY, underlying=underlying, exchange="NFO",
    )


def _order(leg: StrategyLeg, side: OrderSide, quantity: int, price: str) -> PaperOrderRequest:
    return PaperOrderRequest(leg=leg, side=side, quantity=quantity, reference_price=Decimal(price), timestamp=_NOW)


def _account(capital: str = "100000") -> PaperTradingAccount:
    return PaperTradingAccount("acct-1", Decimal(capital), _NO_COST_CONFIG)


class TestOpeningAPosition:
    def test_buy_opens_a_long_position(self) -> None:
        account = _account()
        leg = _leg(LegKind.CALL_BUY)

        account.submit_order(_order(leg, OrderSide.BUY, 10, "100"))

        snapshot = account.snapshot()
        assert len(snapshot.open_positions) == 1
        assert snapshot.open_positions[0].quantity == 10
        assert snapshot.open_positions[0].average_entry_price == Decimal("100")

    def test_buy_reduces_cash_by_notional(self) -> None:
        account = _account("100000")

        account.submit_order(_order(_leg(LegKind.CALL_BUY), OrderSide.BUY, 10, "100"))

        assert account.snapshot().cash_balance == Decimal("100000") - Decimal("1000")

    def test_sell_opens_a_short_position(self) -> None:
        account = _account()

        account.submit_order(_order(_leg(LegKind.CALL_SELL), OrderSide.SELL, 5, "50"))

        snapshot = account.snapshot()
        assert snapshot.open_positions[0].quantity == -5

    def test_sell_increases_cash_by_notional(self) -> None:
        account = _account("100000")

        account.submit_order(_order(_leg(LegKind.CALL_SELL), OrderSide.SELL, 5, "50"))

        assert account.snapshot().cash_balance == Decimal("100000") + Decimal("250")

    def test_equity_unchanged_immediately_after_opening_with_no_price_move(self) -> None:
        """Equity is valued at cost basis (no live mark), so opening a
        position with no price movement yet must leave equity exactly at
        the pre-trade level -- neither double-counting the cost nor
        fabricating unrealized gain."""
        account = _account("100000")

        account.submit_order(_order(_leg(LegKind.CALL_BUY), OrderSide.BUY, 10, "100"))

        assert account.snapshot().equity == Decimal("100000")

    def test_equity_unchanged_after_opening_a_short_with_no_price_move(self) -> None:
        account = _account("100000")

        account.submit_order(_order(_leg(LegKind.CALL_SELL), OrderSide.SELL, 5, "50"))

        assert account.snapshot().equity == Decimal("100000")


class TestAddingToAPosition:
    def test_second_buy_increases_quantity_and_averages_entry_price(self) -> None:
        account = _account()
        leg = _leg(LegKind.CALL_BUY)

        account.submit_order(_order(leg, OrderSide.BUY, 10, "100"))
        account.submit_order(_order(leg, OrderSide.BUY, 10, "120"))

        position = account.snapshot().open_positions[0]
        assert position.quantity == 20
        assert position.average_entry_price == Decimal("110")  # (10*100 + 10*120) / 20


class TestClosingAPosition:
    def test_full_close_realizes_pnl_and_removes_position(self) -> None:
        account = _account()
        leg = _leg(LegKind.CALL_BUY)
        account.submit_order(_order(leg, OrderSide.BUY, 10, "100"))

        account.submit_order(_order(leg, OrderSide.SELL, 10, "130"))

        snapshot = account.snapshot()
        assert snapshot.open_positions == ()
        assert snapshot.realized_pnl == Decimal("300")  # 10 * (130 - 100)

    def test_full_close_leaves_equity_equal_to_cash(self) -> None:
        account = _account("100000")
        leg = _leg(LegKind.CALL_BUY)
        account.submit_order(_order(leg, OrderSide.BUY, 10, "100"))

        account.submit_order(_order(leg, OrderSide.SELL, 10, "130"))

        snapshot = account.snapshot()
        assert snapshot.equity == snapshot.cash_balance == Decimal("100300")  # 100000 + 300 realized

    def test_partial_close_keeps_entry_price_and_reduces_quantity(self) -> None:
        account = _account()
        leg = _leg(LegKind.CALL_BUY)
        account.submit_order(_order(leg, OrderSide.BUY, 10, "100"))

        account.submit_order(_order(leg, OrderSide.SELL, 4, "130"))

        snapshot = account.snapshot()
        assert snapshot.open_positions[0].quantity == 6
        assert snapshot.open_positions[0].average_entry_price == Decimal("100")  # unchanged
        assert snapshot.realized_pnl == Decimal("120")  # 4 * (130 - 100)

    def test_closing_a_short_buys_back_and_realizes_pnl(self) -> None:
        account = _account()
        leg = _leg(LegKind.CALL_SELL)
        account.submit_order(_order(leg, OrderSide.SELL, 10, "100"))  # sold to open at 100

        account.submit_order(_order(leg, OrderSide.BUY, 10, "70"))  # bought back cheaper

        snapshot = account.snapshot()
        assert snapshot.open_positions == ()
        assert snapshot.realized_pnl == Decimal("300")  # 10 * (100 - 70): profit on a short

    def test_reversal_closes_existing_and_opens_opposite_at_fill_price(self) -> None:
        """Selling more than the current long closes it and flips to a
        fresh short, priced at this fill (not blended with the old entry)."""
        account = _account()
        leg = _leg(LegKind.CALL_BUY)
        account.submit_order(_order(leg, OrderSide.BUY, 10, "100"))

        account.submit_order(_order(leg, OrderSide.SELL, 15, "120"))

        snapshot = account.snapshot()
        assert snapshot.open_positions[0].quantity == -5
        assert snapshot.open_positions[0].average_entry_price == Decimal("120")
        assert snapshot.realized_pnl == Decimal("200")  # only the closed 10 realize: 10*(120-100)


class TestMultipleInstrumentsTrackedSeparately:
    def test_different_strikes_are_independent_positions(self) -> None:
        account = _account()
        low = _leg(LegKind.CALL_BUY, strike="24400")
        high = _leg(LegKind.CALL_BUY, strike="24600")

        account.submit_order(_order(low, OrderSide.BUY, 10, "100"))
        account.submit_order(_order(high, OrderSide.BUY, 5, "50"))

        snapshot = account.snapshot()
        assert len(snapshot.open_positions) == 2

    def test_different_underlyings_are_independent_positions(self) -> None:
        account = _account()
        nifty = _leg(LegKind.CALL_BUY, underlying="NIFTY")
        banknifty = _leg(LegKind.CALL_BUY, underlying="BANKNIFTY")

        account.submit_order(_order(nifty, OrderSide.BUY, 10, "100"))
        account.submit_order(_order(banknifty, OrderSide.BUY, 10, "100"))

        assert len(account.snapshot().open_positions) == 2

    def test_call_and_put_at_same_strike_are_independent_positions(self) -> None:
        account = _account()
        call = _leg(LegKind.CALL_BUY)
        put = _leg(LegKind.PUT_BUY)

        account.submit_order(_order(call, OrderSide.BUY, 10, "100"))
        account.submit_order(_order(put, OrderSide.BUY, 10, "100"))

        assert len(account.snapshot().open_positions) == 2


class TestTradeHistory:
    def test_trades_recorded_in_submission_order(self) -> None:
        account = _account()
        leg = _leg(LegKind.CALL_BUY)

        account.submit_order(_order(leg, OrderSide.BUY, 10, "100"))
        account.submit_order(_order(leg, OrderSide.SELL, 10, "130"))

        history = account.trade_history()
        assert len(history) == 2
        assert history[0].side == OrderSide.BUY
        assert history[1].side == OrderSide.SELL
        assert history[1].realized_pnl == Decimal("300")

    def test_opening_trade_has_zero_realized_pnl(self) -> None:
        account = _account()

        account.submit_order(_order(_leg(LegKind.CALL_BUY), OrderSide.BUY, 10, "100"))

        assert account.trade_history()[0].realized_pnl == Decimal("0")


class TestCommissionsAndSlippage:
    def test_commission_reduces_cash_beyond_notional(self) -> None:
        config = ExecutionConfig(
            slippage_pct=Decimal("0"), commission_per_trade=Decimal("20"),
            brokerage_pct=Decimal("0"), exchange_charges_pct=Decimal("0"),
            partial_fill_enabled=False,
        )
        account = PaperTradingAccount("acct-1", Decimal("100000"), config)

        account.submit_order(_order(_leg(LegKind.CALL_BUY), OrderSide.BUY, 10, "100"))

        assert account.snapshot().cash_balance == Decimal("100000") - Decimal("1000") - Decimal("20")

    def test_slippage_moves_the_realized_fill_price(self) -> None:
        config = ExecutionConfig(
            slippage_pct=Decimal("1"), commission_per_trade=Decimal("0"),
            brokerage_pct=Decimal("0"), exchange_charges_pct=Decimal("0"),
            partial_fill_enabled=False,
        )
        account = PaperTradingAccount("acct-1", Decimal("100000"), config)

        trade = account.submit_order(_order(_leg(LegKind.CALL_BUY), OrderSide.BUY, 10, "100"))

        assert trade.fill_price == Decimal("101")  # 100 + 1% slippage, buy pays up


class TestReset:
    def test_reset_via_new_account_clears_state(self) -> None:
        account = _account("100000")
        account.submit_order(_order(_leg(LegKind.CALL_BUY), OrderSide.BUY, 10, "100"))
        assert account.snapshot().open_positions != ()

        fresh = PaperTradingAccount("acct-1", Decimal("50000"), _NO_COST_CONFIG)

        snapshot = fresh.snapshot()
        assert snapshot.open_positions == ()
        assert snapshot.cash_balance == Decimal("50000")
        assert snapshot.realized_pnl == Decimal("0")
