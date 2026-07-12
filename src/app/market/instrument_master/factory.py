"""Build Instrument models from underlying master records."""

from decimal import Decimal

from app.market.enums import ExchangeCode, InstrumentType
from app.market.exchanges.models import UnderlyingMaster
from app.market.instrument_master.models import (ExpiryRulesRef, Instrument,
                                                 InstrumentSpecification,
                                                 TradingHoursRef)


class InstrumentFactory:
    """Create instrument records from underlying definitions."""

    @staticmethod
    def from_underlying(underlying: UnderlyingMaster) -> Instrument:
        """Create an index instrument from an underlying master record."""
        instrument_id = f"{underlying.exchange.value}:{underlying.symbol}"
        spec = InstrumentSpecification(
            tick_size=underlying.tick_size,
            lot_size=underlying.lot_size,
            freeze_quantity=underlying.freeze_quantity,
            strike_interval=underlying.strike_interval,
            price_precision=underlying.price_precision,
            quantity_precision=underlying.quantity_precision,
            contract_multiplier=underlying.contract_multiplier,
        )
        expiry_rules = ExpiryRulesRef(
            weekly_expiry_day=underlying.weekly_expiry_day,
            monthly_expiry_day=underlying.monthly_expiry_day,
            supports_weekly=underlying.weekly_expiry_day is not None,
            supports_monthly=underlying.monthly_expiry_day is not None,
        )
        return Instrument(
            instrument_id=instrument_id,
            trading_symbol=underlying.symbol,
            display_name=underlying.display_name,
            underlying=underlying.symbol,
            exchange=underlying.exchange,
            segment=underlying.segment,
            instrument_type=InstrumentType(underlying.instrument_type),
            specification=spec,
            trading_hours=TradingHoursRef(),
            expiry_rules=expiry_rules,
            is_active=underlying.is_active,
        )

    @staticmethod
    def placeholder(
        symbol: str,
        *,
        exchange: ExchangeCode,
        instrument_type: InstrumentType,
        category: str,
    ) -> Instrument:
        """Create a placeholder instrument for future asset classes."""
        return Instrument(
            instrument_id=f"{exchange.value}:{symbol}",
            trading_symbol=symbol,
            display_name=f"{symbol} ({category})",
            underlying=symbol,
            exchange=exchange,
            segment="FO",
            instrument_type=instrument_type,
            specification=InstrumentSpecification(
                tick_size=Decimal("0.05"),
                lot_size=1,
                freeze_quantity=1,
                strike_interval=Decimal("1"),
            ),
            is_active=False,
        )
