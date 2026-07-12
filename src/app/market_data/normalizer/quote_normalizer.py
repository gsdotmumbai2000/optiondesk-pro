"""Normalize broker quotes into market data models."""

from datetime import datetime, timezone
from decimal import Decimal

from app.brokers.shared.models import Quote as BrokerQuote
from app.market_data.models import Ask, Bid, Depth, FutureQuote, IndexQuote, OHLC, Quote
from app.market_data.models.enums import InstrumentKind


def normalize_quote(
    broker_quote: BrokerQuote,
    *,
    underlying: str = "",
    instrument_kind: InstrumentKind = InstrumentKind.SPOT,
    expiry_date: str = "",
    strike_price: Decimal | None = None,
    option_right: str = "",
) -> Quote:
    """Convert broker quote to enterprise quote."""
    return Quote(
        symbol=broker_quote.symbol,
        exchange=broker_quote.exchange,
        underlying=underlying or broker_quote.symbol,
        instrument_kind=instrument_kind,
        ltp=broker_quote.ltp,
        ohlc=OHLC(
            open=broker_quote.open,
            high=broker_quote.high,
            low=broker_quote.low,
            close=broker_quote.close,
        ),
        bid=broker_quote.bid,
        ask=broker_quote.ask,
        depth=Depth(
            bids=[
                Bid(price=level.price, quantity=level.quantity, orders=level.orders)
                for level in broker_quote.bid_depth
            ],
            asks=[
                Ask(price=level.price, quantity=level.quantity, orders=level.orders)
                for level in broker_quote.ask_depth
            ],
        ),
        volume=broker_quote.volume,
        open_interest=broker_quote.open_interest,
        change=broker_quote.change,
        change_percent=broker_quote.change_percent,
        expiry_date=expiry_date,
        strike_price=strike_price,
        option_right=option_right,
        timestamp=broker_quote.timestamp or datetime.now(timezone.utc),
    )


def to_future_quote(quote: Quote) -> FutureQuote:
    """Convert quote to future quote."""
    return FutureQuote(
        symbol=quote.symbol,
        exchange=quote.exchange,
        underlying=quote.underlying,
        expiry_date=quote.expiry_date,
        ltp=quote.ltp,
        ohlc=quote.ohlc,
        volume=quote.volume,
        open_interest=quote.open_interest,
        timestamp=quote.timestamp,
    )


def to_index_quote(quote: Quote) -> IndexQuote:
    """Convert quote to index quote."""
    return IndexQuote(
        symbol=quote.symbol,
        exchange=quote.exchange,
        ltp=quote.ltp,
        ohlc=quote.ohlc,
        change=quote.change,
        change_percent=quote.change_percent,
        timestamp=quote.timestamp,
    )
