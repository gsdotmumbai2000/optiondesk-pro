"""Bridges BrokerInterface.calculate_margin() (broker-shared Margins) into
the margin engine's BrokerMarginResponse, for on-demand real-broker margin
refreshes -- not the tick-driven live pipeline. margin_calculator is a
rate-limited REST call, so it is only invoked when a workspace explicitly
asks for a fresh broker margin (e.g. a "Refresh Margin" action), never on
every live recalculation.
"""

from datetime import datetime, timezone
from decimal import Decimal

from app.brokers.bootstrap import BrokerProvider
from app.brokers.shared.enums import OptionRight, OrderSide, OrderType, ProductType
from app.brokers.shared.exceptions import BrokerNotSupportedException
from app.brokers.shared.models import OrderRequest
from app.exceptions.broker_exception import BrokerException
from app.margin.models.broker_response import BrokerMarginResponse
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg

_BUY_KINDS = frozenset(
    {LegKind.CALL_BUY, LegKind.PUT_BUY, LegKind.FUTURE_BUY, LegKind.STOCK_BUY}
)
_FUTURE_KINDS = frozenset({LegKind.FUTURE_BUY, LegKind.FUTURE_SELL})
_OPTION_RIGHTS = {
    LegKind.CALL_BUY: OptionRight.CALL,
    LegKind.CALL_SELL: OptionRight.CALL,
    LegKind.PUT_BUY: OptionRight.PUT,
    LegKind.PUT_SELL: OptionRight.PUT,
}


class BrokerMarginAdapter:
    """BrokerMarginPort implementation backed by a live BrokerInterface."""

    def __init__(self, broker_provider: BrokerProvider) -> None:
        self._broker_provider = broker_provider

    def calculate_margin(
        self, legs: tuple[StrategyLeg, ...], exchange: str
    ) -> BrokerMarginResponse | None:
        """Return real broker margin for the legs, or None on any failure
        (no legs, not connected, broker doesn't support it, API error) so
        callers fall back to the existing estimated-margin path unchanged."""
        if not legs:
            return None
        broker = self._broker_provider.broker
        if broker is None or not broker.is_connected():
            return None
        try:
            orders = [self._to_order_request(leg, exchange) for leg in legs]
            margins = broker.calculate_margin(orders, exchange)
            if margins is None:
                return None
            funds = broker.get_funds()
        except (BrokerNotSupportedException, BrokerException):
            return None
        return BrokerMarginResponse(
            broker_id=broker.broker_code.value,
            initial_margin=margins.total_margin,
            exposure_margin=margins.exposure_margin,
            span_margin=margins.span_margin,
            total_margin=margins.total_margin,
            available_margin=max(funds.available_cash - margins.total_margin, Decimal("0")),
            account_balance=funds.total_balance,
            captured_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _to_order_request(leg: StrategyLeg, exchange: str) -> OrderRequest:
        side = OrderSide.BUY if leg.kind in _BUY_KINDS else OrderSide.SELL
        option_right = _OPTION_RIGHTS.get(leg.kind)
        if option_right is not None:
            product = ProductType.OPTIONS
        elif leg.kind in _FUTURE_KINDS:
            product = ProductType.FUTURES
        else:
            product = ProductType.CASH
        return OrderRequest(
            symbol=leg.underlying,
            exchange=leg.exchange or exchange,
            product_type=product,
            side=side,
            order_type=OrderType.MARKET,
            quantity=abs(leg.quantity),
            price=leg.premium,
            expiry_date=leg.expiry.strftime("%d-%b-%Y") if leg.expiry else None,
            strike_price=leg.strike if leg.strike > 0 else None,
            option_right=option_right.value if option_right else None,
        )
