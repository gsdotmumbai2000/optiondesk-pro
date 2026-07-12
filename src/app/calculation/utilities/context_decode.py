"""Decode serialized calculation context payloads."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.models.configuration import CalculationConfiguration
from app.calculation.models.enums import ContextVersion, MarketSessionType
from app.calculation.models.market_session import MarketSession
from app.calculation.models.snapshots import (
    FutureQuoteSnapshot,
    OptionChainSnapshot,
    OptionStrikeSnapshot,
    SpotQuoteSnapshot,
)


def decode_context(data: dict[str, Any]) -> CalculationContext:
    """Rebuild a calculation context from encoded data."""
    return CalculationContext(
        underlying=str(data["underlying"]),
        spot_price=_decimal(data["spot_price"]),
        future_price=_optional_decimal(data.get("future_price")),
        underlying_symbol=str(data["underlying_symbol"]),
        exchange=str(data["exchange"]),
        expiry=date.fromisoformat(str(data["expiry"])),
        current_time=datetime.fromisoformat(str(data["current_time"])),
        trade_date=date.fromisoformat(str(data["trade_date"])),
        market_status=str(data["market_status"]),
        interest_rate=_decimal(data["interest_rate"]),
        dividend_yield=_decimal(data["dividend_yield"]),
        risk_free_rate=_decimal(data["risk_free_rate"]),
        volatility=_decimal(data["volatility"]),
        historical_volatility=_optional_decimal(data.get("historical_volatility")),
        implied_volatility=_optional_decimal(data.get("implied_volatility")),
        days_to_expiry=int(data["days_to_expiry"]),
        time_to_expiry=_decimal(data["time_to_expiry"]),
        atm_strike=_decimal(data["atm_strike"]),
        lot_size=int(data["lot_size"]),
        tick_size=_decimal(data["tick_size"]),
        strike_interval=_decimal(data["strike_interval"]),
        currency=str(data["currency"]),
        market_session=_decode_session(data["market_session"]),
        option_chain_snapshot=_decode_chain(data.get("option_chain_snapshot")),
        future_quote=_decode_future(data.get("future_quote")),
        spot_quote=_decode_spot(data["spot_quote"]),
        configuration=_decode_configuration(data["configuration"]),
        calculation_timestamp=datetime.fromisoformat(str(data["calculation_timestamp"])),
        version=ContextVersion(str(data.get("version", ContextVersion.V1.value))),
    )


def _decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _optional_decimal(value: object | None) -> Decimal | None:
    if value is None:
        return None
    return _decimal(value)


def _optional_datetime(value: object | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(str(value))


def _decode_configuration(data: dict[str, Any]) -> CalculationConfiguration:
    return CalculationConfiguration(
        risk_free_rate=str(data.get("risk_free_rate", "default")),
        dividend_model=str(data.get("dividend_model", "none")),
        volatility_model=str(data.get("volatility_model", "implied")),
        calendar_code=str(data.get("calendar_code", "NSE")),
        metadata=dict(data.get("metadata", {})),
    )


def _decode_session(data: dict[str, Any]) -> MarketSession:
    return MarketSession(
        exchange=str(data["exchange"]),
        session_type=MarketSessionType(str(data["session_type"])),
        is_open=bool(data["is_open"]),
        trade_date=str(data.get("trade_date", "")),
    )


def _decode_spot(data: dict[str, Any]) -> SpotQuoteSnapshot:
    return SpotQuoteSnapshot(
        symbol=str(data["symbol"]),
        exchange=str(data["exchange"]),
        ltp=_decimal(data["ltp"]),
        timestamp=_optional_datetime(data.get("timestamp")),
    )


def _decode_future(data: dict[str, Any] | None) -> FutureQuoteSnapshot | None:
    if data is None:
        return None
    return FutureQuoteSnapshot(
        symbol=str(data["symbol"]),
        exchange=str(data["exchange"]),
        underlying=str(data["underlying"]),
        expiry_date=str(data["expiry_date"]),
        ltp=_decimal(data["ltp"]),
        open_interest=data.get("open_interest"),
        volume=data.get("volume"),
        timestamp=_optional_datetime(data.get("timestamp")),
    )


def _decode_chain(data: dict[str, Any] | None) -> OptionChainSnapshot | None:
    if data is None:
        return None
    strikes = tuple(_decode_strike(item) for item in data.get("strikes", []))
    return OptionChainSnapshot(
        underlying=str(data["underlying"]),
        exchange=str(data["exchange"]),
        expiry_date=str(data["expiry_date"]),
        spot_price=_optional_decimal(data.get("spot_price")),
        atm_strike=_optional_decimal(data.get("atm_strike")),
        strikes=strikes,
    )


def _decode_strike(data: dict[str, Any]) -> OptionStrikeSnapshot:
    return OptionStrikeSnapshot(
        strike_price=_decimal(data["strike_price"]),
        call_ltp=_optional_decimal(data.get("call_ltp")),
        put_ltp=_optional_decimal(data.get("put_ltp")),
        call_oi=data.get("call_oi"),
        put_oi=data.get("put_oi"),
        call_iv=_optional_decimal(data.get("call_iv")),
        put_iv=_optional_decimal(data.get("put_iv")),
        is_atm=bool(data.get("is_atm", False)),
    )
