"""Tests for BrokerMarginAdapter: the bridge from BrokerInterface.calculate_
margin() (broker-shared Margins) into the margin engine's
BrokerMarginResponse, used for on-demand real-broker margin refreshes.
"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.application.services.broker_margin_adapter import BrokerMarginAdapter
from app.brokers.shared.enums import BrokerCode
from app.brokers.shared.exceptions import BrokerNotSupportedException
from app.brokers.shared.models.portfolio import Funds, Margins
from app.exceptions.broker_exception import BrokerException
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg


def _leg(
    kind: LegKind,
    quantity: int,
    *,
    strike: Decimal = Decimal("24500"),
    expiry: date | None = date(2026, 8, 18),
    premium: Decimal = Decimal("100"),
    underlying: str = "NIFTY",
) -> StrategyLeg:
    return StrategyLeg(
        leg_id="L1", kind=kind, quantity=quantity, premium=premium,
        strike=strike, expiry=expiry, underlying=underlying, exchange="NFO",
    )


class _FakeBroker:
    """Duck-typed BrokerInterface stand-in recording the exact requests it
    receives, so the leg -> OrderRequest mapping is verified directly."""

    def __init__(self, *, connected: bool = True) -> None:
        self._connected = connected
        self.received_positions = None
        self.received_exchange = None
        self.margin_response = Margins(
            exchange="NFO", span_margin=Decimal("7000"),
            exposure_margin=Decimal("2000"), additional_margin=Decimal("0"),
            total_margin=Decimal("9000"),
        )
        self.funds_response = Funds(available_cash=Decimal("50000"), total_balance=Decimal("100000"))
        self.margin_error: Exception | None = None
        self.broker_code = BrokerCode.BREEZE
        self.get_funds_called = False

    def is_connected(self) -> bool:
        return self._connected

    def calculate_margin(self, positions, exchange_code):
        if self.margin_error is not None:
            raise self.margin_error
        self.received_positions = positions
        self.received_exchange = exchange_code
        return self.margin_response

    def get_funds(self) -> Funds:
        self.get_funds_called = True
        return self.funds_response


def _adapter(broker: _FakeBroker | None) -> BrokerMarginAdapter:
    provider = SimpleNamespace(broker=broker)
    return BrokerMarginAdapter(provider)


class TestBrokerMarginAdapterGuardConditions:
    def test_no_legs_returns_none(self) -> None:
        adapter = _adapter(_FakeBroker())

        assert adapter.calculate_margin((), "NFO") is None

    def test_broker_not_connected_returns_none(self) -> None:
        adapter = _adapter(_FakeBroker(connected=False))
        leg = _leg(LegKind.CALL_SELL, 75)

        assert adapter.calculate_margin((leg,), "NFO") is None

    def test_broker_not_supported_returns_none_not_raises(self) -> None:
        broker = _FakeBroker()
        broker.margin_error = BrokerNotSupportedException("Dhan broker is not yet implemented")
        adapter = _adapter(broker)
        leg = _leg(LegKind.CALL_SELL, 75)

        assert adapter.calculate_margin((leg,), "NFO") is None

    def test_broker_returns_none_margin_propagates_as_none_without_calling_get_funds(self) -> None:
        """When calculate_margin() itself returns None (Breeze had no real
        margin to report -- see normalize_margin), the adapter must not
        treat that as success: no get_funds() call, no fabricated
        BrokerMarginResponse with a misleading 0."""
        broker = _FakeBroker()
        broker.margin_response = None
        adapter = _adapter(broker)
        leg = _leg(LegKind.CALL_SELL, 75)

        result = adapter.calculate_margin((leg,), "NFO")

        assert result is None
        assert broker.get_funds_called is False

    def test_broker_exception_returns_none_not_raises(self) -> None:
        broker = _FakeBroker()
        broker.margin_error = BrokerException("API error")
        adapter = _adapter(broker)
        leg = _leg(LegKind.CALL_SELL, 75)

        assert adapter.calculate_margin((leg,), "NFO") is None


class TestBrokerMarginAdapterSuccessfulLookup:
    def test_maps_margins_and_funds_into_broker_margin_response(self) -> None:
        broker = _FakeBroker()
        adapter = _adapter(broker)
        leg = _leg(LegKind.CALL_SELL, 75)

        result = adapter.calculate_margin((leg,), "NFO")

        assert result is not None
        assert result.broker_id == "BREEZE"
        assert result.span_margin == Decimal("7000")
        assert result.exposure_margin == Decimal("2000")
        assert result.total_margin == Decimal("9000")
        assert result.initial_margin == Decimal("9000")
        assert result.account_balance == Decimal("100000")
        assert result.available_margin == Decimal("50000") - Decimal("9000")

    def test_available_margin_clamped_at_zero_when_margin_exceeds_cash(self) -> None:
        broker = _FakeBroker()
        broker.funds_response = Funds(available_cash=Decimal("1000"), total_balance=Decimal("1000"))
        adapter = _adapter(broker)
        leg = _leg(LegKind.CALL_SELL, 75)

        result = adapter.calculate_margin((leg,), "NFO")

        assert result.available_margin == Decimal("0")

    def test_short_call_leg_maps_to_sell_action_call_right_options_product(self) -> None:
        broker = _FakeBroker()
        adapter = _adapter(broker)
        leg = _leg(LegKind.CALL_SELL, 75, strike=Decimal("24500"), expiry=date(2026, 8, 18))

        adapter.calculate_margin((leg,), "NFO")

        order = broker.received_positions[0]
        assert order.side.value == "SELL"
        assert order.option_right == "CALL"
        assert order.product_type.value == "OPTIONS"
        assert order.quantity == 75
        assert order.strike_price == Decimal("24500")
        assert order.expiry_date == "18-Aug-2026"
        assert order.symbol == "NIFTY"

    def test_long_put_leg_maps_to_buy_action_put_right(self) -> None:
        broker = _FakeBroker()
        adapter = _adapter(broker)
        leg = _leg(LegKind.PUT_BUY, 50, strike=Decimal("24000"))

        adapter.calculate_margin((leg,), "NFO")

        order = broker.received_positions[0]
        assert order.side.value == "BUY"
        assert order.option_right == "PUT"

    def test_negative_quantity_magnitude_is_used_for_order_quantity(self) -> None:
        """StrategyLeg quantities may already carry a sign (e.g. from
        to_payoff_legs conversion); the broker order quantity is always
        positive, direction comes from side."""
        broker = _FakeBroker()
        adapter = _adapter(broker)
        leg = _leg(LegKind.CALL_SELL, -75)

        adapter.calculate_margin((leg,), "NFO")

        assert broker.received_positions[0].quantity == 75

    def test_multiple_legs_all_sent_in_one_basket(self) -> None:
        broker = _FakeBroker()
        adapter = _adapter(broker)
        legs = (
            _leg(LegKind.CALL_BUY, 75, strike=Decimal("24400")),
            _leg(LegKind.CALL_SELL, 75, strike=Decimal("24600")),
            _leg(LegKind.PUT_BUY, 75, strike=Decimal("24300")),
            _leg(LegKind.PUT_SELL, 75, strike=Decimal("24200")),
        )

        adapter.calculate_margin(legs, "NFO")

        assert len(broker.received_positions) == 4
        assert broker.received_exchange == "NFO"

    def test_leg_without_expiry_sends_no_expiry_date(self) -> None:
        broker = _FakeBroker()
        adapter = _adapter(broker)
        leg = _leg(LegKind.CALL_SELL, 75, expiry=None)

        adapter.calculate_margin((leg,), "NFO")

        assert broker.received_positions[0].expiry_date is None
