"""Normalize broker option chain data."""

from decimal import Decimal

from app.brokers.shared.models import OptionChain as BrokerOptionChain
from app.market_data.models import OptionChain, OptionStrike


def normalize_option_chain(broker_chain: BrokerOptionChain) -> OptionChain:
    """Convert broker option chain to enterprise model."""
    strikes = [
        OptionStrike(
            strike_price=leg.strike_price,
            expiry_date=broker_chain.expiry_date,
            call_symbol=leg.call_symbol,
            put_symbol=leg.put_symbol,
            call_ltp=leg.call_ltp,
            put_ltp=leg.put_ltp,
            call_oi=leg.call_oi,
            put_oi=leg.put_oi,
            call_volume=leg.call_volume,
            put_volume=leg.put_volume,
            call_iv=leg.call_iv,
            put_iv=leg.put_iv,
            call_delta=leg.call_delta,
            put_delta=leg.put_delta,
            is_atm=leg.is_atm,
        )
        for leg in broker_chain.rows
    ]
    return OptionChain(
        underlying=broker_chain.underlying,
        exchange=broker_chain.exchange,
        expiry_date=broker_chain.expiry_date,
        spot_price=broker_chain.spot_price,
        atm_strike=broker_chain.atm_strike,
        strikes=strikes,
    )
