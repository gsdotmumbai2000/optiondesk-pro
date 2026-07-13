"""Build market data models from live chain."""

from decimal import Decimal

from app.live.models.option_chain import LiveOptionChain
from app.market_data.models.option import OptionChain, OptionStrike


class ChainBuilder:
    """Convert live chain to market data option chain."""

    @staticmethod
    def to_market_chain(chain: LiveOptionChain) -> OptionChain:
        strikes = []
        for row in chain.strike_list():
            strikes.append(
                OptionStrike(
                    strike_price=row.strike_price,
                    expiry_date=chain.expiry_date,
                    call_ltp=row.call.ltp if row.call else None,
                    put_ltp=row.put.ltp if row.put else None,
                    call_oi=row.call.open_interest if row.call else None,
                    put_oi=row.put.open_interest if row.put else None,
                    call_iv=row.call.implied_volatility if row.call else None,
                    put_iv=row.put.implied_volatility if row.put else None,
                    is_atm=row.is_atm,
                )
            )
        return OptionChain(
            underlying=chain.underlying,
            exchange=chain.exchange,
            expiry_date=chain.expiry_date,
            spot_price=chain.spot_price,
            atm_strike=chain.atm_strike,
            strikes=strikes,
        )

    @staticmethod
    def to_snapshot(chain: LiveOptionChain):
        """Convert live chain to calculation snapshot."""
        from app.calculation.models.snapshots import OptionChainSnapshot, OptionStrikeSnapshot

        strikes = tuple(
            OptionStrikeSnapshot(
                strike_price=row.strike_price,
                call_ltp=row.call.ltp if row.call else None,
                put_ltp=row.put.ltp if row.put else None,
                call_oi=row.call.open_interest if row.call else None,
                put_oi=row.put.open_interest if row.put else None,
                call_iv=row.call.implied_volatility if row.call else None,
                put_iv=row.put.implied_volatility if row.put else None,
                is_atm=row.is_atm,
            )
            for row in chain.strike_list()
        )
        return OptionChainSnapshot(
            underlying=chain.underlying,
            exchange=chain.exchange,
            expiry_date=chain.expiry_date,
            spot_price=chain.spot_price,
            atm_strike=chain.atm_strike,
            strikes=strikes,
        )
