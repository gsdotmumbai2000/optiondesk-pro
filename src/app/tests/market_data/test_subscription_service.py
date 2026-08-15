"""Tests for subscription identity, including CALL/PUT key collision fix."""

from app.brokers.shared.enums import ProductType
from app.market_data.subscriptions.subscription_service import SubscriptionService


class _FakeBroker:
    """Records subscribe/unsubscribe calls without touching a real broker."""

    def __init__(self) -> None:
        self.subscribed: list = []
        self.unsubscribed: list = []

    def subscribe_quotes(self, subscription) -> None:
        self.subscribed.append(subscription)

    def unsubscribe_quotes(self, subscription) -> None:
        self.unsubscribed.append(subscription)


def _service() -> tuple[SubscriptionService, _FakeBroker]:
    broker = _FakeBroker()
    return SubscriptionService(broker, can_subscribe=lambda: True), broker


class TestOptionSubscriptionKeyCollision:
    """CALL and PUT subscriptions at the same strike must coexist."""

    def test_call_and_put_subscriptions_at_same_strike_coexist(self) -> None:
        service, broker = _service()

        service.subscribe(
            "NIFTY", "NFO", product_type=ProductType.OPTIONS,
            expiry_date="13-Feb-2026", strike_price="24500", option_right="CALL",
        )
        service.subscribe(
            "NIFTY", "NFO", product_type=ProductType.OPTIONS,
            expiry_date="13-Feb-2026", strike_price="24500", option_right="PUT",
        )

        assert service.active_count() == 2
        assert len(broker.subscribed) == 2
        assert {sub.option_right for sub in broker.subscribed} == {"CALL", "PUT"}

    def test_resubscribing_same_call_does_not_duplicate(self) -> None:
        service, _broker = _service()

        for _ in range(2):
            service.subscribe(
                "NIFTY", "NFO", product_type=ProductType.OPTIONS,
                expiry_date="13-Feb-2026", strike_price="24500", option_right="CALL",
            )

        assert service.active_count() == 1

    def test_unsubscribe_targets_only_matching_option_right(self) -> None:
        service, _broker = _service()
        service.subscribe(
            "NIFTY", "NFO", product_type=ProductType.OPTIONS,
            expiry_date="13-Feb-2026", strike_price="24500", option_right="CALL",
        )
        service.subscribe(
            "NIFTY", "NFO", product_type=ProductType.OPTIONS,
            expiry_date="13-Feb-2026", strike_price="24500", option_right="PUT",
        )

        service.unsubscribe(
            "NIFTY", "NFO", product_type=ProductType.OPTIONS,
            expiry_date="13-Feb-2026", strike_price="24500", option_right="CALL",
        )

        assert service.active_count() == 1

    def test_different_strikes_same_right_coexist(self) -> None:
        service, _broker = _service()

        service.subscribe(
            "NIFTY", "NFO", product_type=ProductType.OPTIONS,
            expiry_date="13-Feb-2026", strike_price="24500", option_right="CALL",
        )
        service.subscribe(
            "NIFTY", "NFO", product_type=ProductType.OPTIONS,
            expiry_date="13-Feb-2026", strike_price="24600", option_right="CALL",
        )

        assert service.active_count() == 2


class TestFutureSubscriptionKeyCollision:
    """Future subscriptions must not collide with options/cash, and must dedupe."""

    def test_future_and_option_subscriptions_at_same_underlying_coexist(self) -> None:
        service, broker = _service()

        service.subscribe(
            "NIFTY", "NFO", product_type=ProductType.FUTURES, expiry_date="18-Aug-2026",
        )
        service.subscribe(
            "NIFTY", "NFO", product_type=ProductType.OPTIONS,
            expiry_date="18-Aug-2026", strike_price="24500", option_right="CALL",
        )

        assert service.active_count() == 2
        assert len(broker.subscribed) == 2
        assert {sub.product_type for sub in broker.subscribed} == {
            ProductType.FUTURES, ProductType.OPTIONS,
        }

    def test_resubscribing_same_future_does_not_duplicate(self) -> None:
        """Repeated calls for the same underlying/exchange/expiry (e.g. one per
        calculation cycle) must not re-hit the broker — proves 534 calculation
        attempts cannot produce 534 broker subscriptions."""
        service, broker = _service()

        for _ in range(534):
            service.subscribe(
                "NIFTY", "NFO", product_type=ProductType.FUTURES, expiry_date="18-Aug-2026",
            )

        assert service.active_count() == 1
        assert len(broker.subscribed) == 1

    def test_future_subscription_changes_identity_when_expiry_changes(self) -> None:
        """A new expiry (e.g. rollover to the next contract) must subscribe as
        a distinct instrument, not silently reuse the old expiry's identity."""
        service, broker = _service()

        service.subscribe(
            "NIFTY", "NFO", product_type=ProductType.FUTURES, expiry_date="18-Aug-2026",
        )
        service.subscribe(
            "NIFTY", "NFO", product_type=ProductType.FUTURES, expiry_date="25-Aug-2026",
        )

        assert service.active_count() == 2
        assert len(broker.subscribed) == 2
        assert {sub.expiry_date for sub in broker.subscribed} == {"18-Aug-2026", "25-Aug-2026"}


class TestCashIndexSubscriptionRegression:
    """NIFTY/BANKNIFTY/FINNIFTY/MIDCPNIFTY cash subscriptions remain unaffected."""

    def test_cash_index_subscriptions_all_activate_independently(self) -> None:
        service, broker = _service()

        for symbol in ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"):
            service.subscribe(symbol, "NSE", product_type=ProductType.CASH)

        assert service.active_count() == 4
        assert len(broker.subscribed) == 4

    def test_resubscribing_same_cash_index_does_not_duplicate(self) -> None:
        service, _broker = _service()

        service.subscribe("NIFTY", "NSE", product_type=ProductType.CASH)
        service.subscribe("NIFTY", "NSE", product_type=ProductType.CASH)

        assert service.active_count() == 1
