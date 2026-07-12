"""Normalize Breeze portfolio responses."""

from decimal import Decimal
from typing import Any

from app.brokers.breeze.utilities import to_decimal, to_int, unwrap_success
from app.brokers.shared.models import BrokerProfile, Funds, Holding, Position


def normalize_profile(broker_code: str, response: dict[str, Any]) -> BrokerProfile:
    """Convert customer details to BrokerProfile."""
    data = unwrap_success(response)
    if not isinstance(data, dict):
        data = {}
    return BrokerProfile(
        broker_code=broker_code,
        account_id=str(data.get("idirect_userid", "")),
        user_name=str(data.get("idirect_user_name", "")),
        email=str(data.get("idirect_user_email", "")),
        segments_allowed=_dict(data.get("segments_allowed")),
        exchange_status=_dict(data.get("exg_status")),
        raw_metadata={key: str(value) for key, value in data.items()},
    )


def normalize_funds(response: dict[str, Any]) -> Funds:
    """Convert funds response to Funds."""
    data = unwrap_success(response)
    if not isinstance(data, dict):
        data = {}
    return Funds(
        available_cash=to_decimal(data.get("total_bank_balance")) or Decimal("0"),
        used_margin=to_decimal(data.get("allocated_equity")) or Decimal("0"),
        total_balance=to_decimal(data.get("total_bank_balance")) or Decimal("0"),
        segments={
            key: to_decimal(value) or Decimal("0")
            for key, value in data.items()
            if "margin" in key.lower() or "balance" in key.lower()
        },
    )


def normalize_holdings(response: dict[str, Any]) -> list[Holding]:
    """Convert holdings response to domain holdings."""
    data = unwrap_success(response)
    rows = data if isinstance(data, list) else []
    holdings: list[Holding] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        holdings.append(
            Holding(
                symbol=str(row.get("stock_code", "")),
                exchange=str(row.get("exchange_code", "")),
                quantity=to_int(row.get("quantity")) or 0,
                average_price=to_decimal(row.get("average_price")) or Decimal("0"),
                current_price=to_decimal(row.get("current_market_price")),
                pnl=to_decimal(row.get("pnl")),
            )
        )
    return holdings


def normalize_positions(response: dict[str, Any]) -> list[Position]:
    """Convert positions response to domain positions."""
    data = unwrap_success(response)
    rows = data if isinstance(data, list) else []
    positions: list[Position] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        positions.append(
            Position(
                symbol=str(row.get("stock_code", "")),
                exchange=str(row.get("exchange_code", "")),
                product_type=str(row.get("product_type", "")),
                quantity=to_int(row.get("quantity")) or 0,
                average_price=to_decimal(row.get("average_price")) or Decimal("0"),
                ltp=to_decimal(row.get("ltp")),
                mtm=to_decimal(row.get("mtm")),
                pnl=to_decimal(row.get("pnl")),
                expiry_date=str(row.get("expiry_date", "") or ""),
                strike_price=to_decimal(row.get("strike_price")),
                option_right=str(row.get("right", "") or ""),
            )
        )
    return positions


def _dict(value: Any) -> dict[str, str]:
    """Convert mapping values to strings."""
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items()}
