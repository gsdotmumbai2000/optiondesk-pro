"""Build immutable snapshots from market data query port."""

from decimal import Decimal

from app.calculation.exceptions import MissingMarketDataException
from app.calculation.models.snapshots import (
    FutureQuoteSnapshot,
    OptionChainSnapshot,
    OptionStrikeSnapshot,
    SpotQuoteSnapshot,
)
from app.calculation.providers.ports import IMarketDataQueryPort


class MarketSnapshotBuilder:
    """Convert market data query results into calculation snapshots."""

    def __init__(self, market_data: IMarketDataQueryPort) -> None:
        """Initialize builder."""
        self._market_data = market_data

    def spot(self, symbol: str, exchange: str) -> SpotQuoteSnapshot:
        """Build spot quote snapshot."""
        quote = self._market_data.get_spot(symbol, exchange)
        ltp = getattr(quote, "ltp", None)
        if ltp is None:
            raise MissingMarketDataException(f"Spot quote unavailable: {symbol}")
        return SpotQuoteSnapshot(
            symbol=symbol.upper(),
            exchange=exchange.upper(),
            ltp=Decimal(str(ltp)),
            timestamp=getattr(quote, "timestamp", None),
        )

    def future(
        self,
        symbol: str,
        exchange: str,
        expiry_date: str,
    ) -> FutureQuoteSnapshot:
        """Build future quote snapshot."""
        quote = self._market_data.get_future(symbol, exchange, expiry_date)
        ltp = getattr(quote, "ltp", None)
        if ltp is None:
            raise MissingMarketDataException(f"Future quote unavailable: {symbol}")
        return FutureQuoteSnapshot(
            symbol=symbol.upper(),
            exchange=exchange.upper(),
            underlying=str(getattr(quote, "underlying", symbol)).upper(),
            expiry_date=expiry_date,
            ltp=Decimal(str(ltp)),
            open_interest=getattr(quote, "open_interest", None),
            volume=getattr(quote, "volume", None),
            timestamp=getattr(quote, "timestamp", None),
        )

    def option_chain(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
    ) -> OptionChainSnapshot:
        """Build option chain snapshot."""
        chain = self._market_data.get_option_chain(underlying, exchange, expiry_date)
        strikes = tuple(self._strike_snapshot(leg) for leg in chain.strikes)
        spot = chain.spot_price
        atm = chain.atm_strike
        return OptionChainSnapshot(
            underlying=underlying.upper(),
            exchange=exchange.upper(),
            expiry_date=expiry_date,
            spot_price=Decimal(str(spot)) if spot is not None else None,
            atm_strike=Decimal(str(atm)) if atm is not None else None,
            strikes=strikes,
        )

    @staticmethod
    def atm_implied_volatility(chain: OptionChainSnapshot) -> Decimal | None:
        """Return ATM implied volatility from a chain snapshot."""
        for leg in chain.strikes:
            if leg.is_atm:
                return leg.call_iv or leg.put_iv
        return None

    @staticmethod
    def _strike_snapshot(leg: object) -> OptionStrikeSnapshot:
        return OptionStrikeSnapshot(
            strike_price=Decimal(str(leg.strike_price)),
            call_ltp=Decimal(str(leg.call_ltp)) if leg.call_ltp is not None else None,
            put_ltp=Decimal(str(leg.put_ltp)) if leg.put_ltp is not None else None,
            call_oi=leg.call_oi,
            put_oi=leg.put_oi,
            call_iv=Decimal(str(leg.call_iv)) if leg.call_iv is not None else None,
            put_iv=Decimal(str(leg.put_iv)) if leg.put_iv is not None else None,
            is_atm=leg.is_atm,
        )
