"""Buying power calculation."""

from decimal import Decimal

from app.margin.models.broker_response import BrokerMarginResponse


def buying_power(
    response: BrokerMarginResponse,
    leverage_factor: Decimal = Decimal("1"),
) -> Decimal:
    """Compute buying power from available margin."""
    return response.available_margin * leverage_factor


def margin_utilization(
    response: BrokerMarginResponse,
) -> Decimal:
    """Compute margin utilization as fraction of account."""
    if response.account_balance <= 0:
        return Decimal("0")
    return min(response.total_margin / response.account_balance, Decimal("1"))
