"""WebSocket lifecycle for live market data."""

from datetime import datetime, timezone
from threading import RLock
from typing import Any

from app.brokers.broker_interface.interface import BrokerInterface
from app.brokers.breeze.normalizers.exchange_normalizer import canonical_exchange
from app.brokers.breeze.normalizers.quote_normalizer import normalize_quote as breeze_quote
from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger
from app.market_data.diagnostics import is_index_related_text, log_tick_diagnostic
from app.market_data.dispatcher.event_dispatcher import EventDispatcher
from app.market_data.models.quote import OHLC
from app.market_data.models.tick import TickSnapshot
from app.market_data.symbols import (
    CanonicalSymbol,
    InstrumentMasterSymbolCanonicalizer,
    SymbolCanonicalizer,
    build_option_contract_symbol,
)
from app.market_data.websocket.enums import LiveConnectionStatus

logger = get_logger(__name__)


class WebSocketService:
    """Manage single broker websocket connection for live ticks."""

    def __init__(
        self,
        broker: BrokerInterface,
        dispatcher: EventDispatcher,
        event_bus: EventBus | None = None,
        symbol_canonicalizer: SymbolCanonicalizer | None = None,
    ) -> None:
        """Initialize websocket service."""
        self._broker = broker
        self._dispatcher = dispatcher
        self._event_bus = event_bus
        self._symbol_canonicalizer = (
            symbol_canonicalizer or InstrumentMasterSymbolCanonicalizer()
        )
        self._lock = RLock()
        self._status = LiveConnectionStatus.DISCONNECTED
        self._last_message: datetime | None = None

    @property
    def status(self) -> LiveConnectionStatus:
        """Return websocket connection status."""
        with self._lock:
            return self._status

    @property
    def last_message(self) -> datetime | None:
        """Return last websocket message time."""
        with self._lock:
            return self._last_message

    def connect(self) -> None:
        """Connect websocket feed via broker."""
        if not self._broker.is_connected():
            return
        with self._lock:
            self._status = LiveConnectionStatus.CONNECTING
        self._attach_handler()
        with self._lock:
            self._status = LiveConnectionStatus.CONNECTED
        logger.info("Market data websocket connected")

    def disconnect(self) -> None:
        """Disconnect websocket feed."""
        with self._lock:
            self._status = LiveConnectionStatus.DISCONNECTED
        logger.info("Market data websocket disconnected")

    def on_broker_connected(self) -> None:
        """Handle broker reconnect."""
        self._attach_handler()
        with self._lock:
            self._status = LiveConnectionStatus.CONNECTED

    def on_broker_disconnected(self) -> None:
        """Handle broker disconnect."""
        with self._lock:
            self._status = LiveConnectionStatus.DISCONNECTED

    def _attach_handler(self) -> None:
        websocket = getattr(self._broker, "_websocket", None)
        if websocket is None:
            return
        websocket.set_quote_handler(self._on_raw_ticks)

    def _on_raw_ticks(self, payload: Any) -> None:
        ticks = payload if isinstance(payload, list) else [payload]
        for item in ticks:
            self._process_tick(item)

    def _process_tick(self, item: Any) -> None:
        if not isinstance(item, dict):
            return
        symbol = str(item.get("stock_code") or item.get("symbol") or "")
        exchange = canonical_exchange(str(item.get("exchange_code") or item.get("exchange") or "NSE"))
        if not symbol:
            return
        raw_product_type = str(item.get("product_type", ""))
        raw_stock_name = str(item.get("stock_name") or item.get("display_name") or "")
        raw_ltp = item.get("ltp") or item.get("last_price") or item.get("last") or item.get("last_trade_price")
        # TEMPORARY DIAGNOSTIC (NIFTY spot-unavailable trace) - boundary 1:
        # raw Breeze SDK callback fields, cash/index-related ticks only.
        if is_index_related_text(symbol) or is_index_related_text(raw_stock_name):
            logger.debug(
                "[DIAG-1 RAW-SDK] stock_code={stock_code!r} exchange_code={exchange_code!r} "
                "product_type={product_type!r} stock_name={stock_name!r} strike_price={strike_price!r} "
                "right={right!r} ltp={ltp!r}",
                stock_code=symbol,
                exchange_code=exchange,
                product_type=raw_product_type,
                stock_name=raw_stock_name,
                strike_price=item.get("strike_price", ""),
                right=item.get("right", ""),
                ltp=raw_ltp,
            )
            # TEMPORARY DIAGNOSTIC (NIFTY spot-unavailable trace) - boundary 1b:
            # the untouched raw dict keys, so "stock_code" above is never
            # mistaken for a literal payload key when it was actually a
            # fallback to item["symbol"].
            logger.debug(
                "[DIAG-1B RAW-KEYS] raw_symbol={raw_symbol!r} raw_stock_code={raw_stock_code!r} "
                "raw_stock_name={raw_stock_name!r} raw_exchange={raw_exchange!r} "
                "raw_exchange_code={raw_exchange_code!r} raw_product_type={raw_product_type!r} "
                "raw_right={raw_right!r} raw_strike_price={raw_strike_price!r} "
                "raw_ltp={raw_ltp!r} raw_last={raw_last!r} raw_last_price={raw_last_price!r} "
                "raw_last_trade_price={raw_last_trade_price!r} all_keys={all_keys!r}",
                raw_symbol=item.get("symbol"),
                raw_stock_code=item.get("stock_code"),
                raw_stock_name=item.get("stock_name"),
                raw_exchange=item.get("exchange"),
                raw_exchange_code=item.get("exchange_code"),
                raw_product_type=item.get("product_type"),
                raw_right=item.get("right"),
                raw_strike_price=item.get("strike_price"),
                raw_ltp=item.get("ltp"),
                raw_last=item.get("last"),
                raw_last_price=item.get("last_price"),
                raw_last_trade_price=item.get("last_trade_price"),
                all_keys=sorted(item.keys()),
            )
        broker_quote = breeze_quote(symbol, exchange, item)
        option_right = str(item.get("right", ""))
        strike_price = str(item.get("strike_price", ""))
        if option_right and strike_price:
            canonical = self._canonicalize_option_tick(
                item, broker_quote, option_right=option_right, strike_price=strike_price
            )
        else:
            canonical = self._symbol_canonicalizer.canonicalize(
                broker_quote.symbol,
                exchange=broker_quote.exchange,
                broker_code=self._broker.broker_code.value,
            )
        tick = TickSnapshot(
            symbol=canonical.symbol,
            broker_symbol=canonical.broker_symbol,
            exchange=broker_quote.exchange,
            ltp=broker_quote.ltp,
            ohlc=OHLC(
                open=broker_quote.open,
                high=broker_quote.high,
                low=broker_quote.low,
                close=broker_quote.close,
            ),
            volume=broker_quote.volume,
            open_interest=broker_quote.open_interest,
            bid=broker_quote.bid,
            ask=broker_quote.ask,
            change=broker_quote.change,
            timestamp=broker_quote.timestamp,
            product_type=str(item.get("product_type", "")),
            expiry_date=str(item.get("expiry_date", "")),
            strike_price=str(item.get("strike_price", "")),
            option_right=str(item.get("right", "")),
        )
        # TEMPORARY DIAGNOSTIC (NIFTY spot-unavailable trace) - boundary 2:
        # raw symbol vs normalized/canonical symbol, cash/index-related ticks only.
        if is_index_related_text(symbol) or is_index_related_text(raw_stock_name) or is_index_related_text(tick.symbol):
            logger.debug(
                "[DIAG-2 NORMALIZED] raw_symbol={raw_symbol!r} normalized_symbol={normalized_symbol!r} "
                "exchange={exchange!r} instrument_kind={instrument_kind!r} ltp={ltp!r}",
                raw_symbol=canonical.broker_symbol,
                normalized_symbol=canonical.symbol,
                exchange=tick.exchange,
                instrument_kind="OPTION" if tick.strike_price else "CASH_INDEX",
                ltp=tick.ltp,
            )
        self._dispatcher.enqueue(tick)
        log_tick_diagnostic(logger, "WEBSOCKET", "tick received", tick)
        with self._lock:
            self._last_message = datetime.now(timezone.utc)

    def _canonicalize_option_tick(
        self,
        item: dict,
        broker_quote: Any,
        *,
        option_right: str,
        strike_price: str,
    ) -> CanonicalSymbol:
        """Build a canonical option contract symbol for an option tick.

        Breeze identifies option ticks with an opaque internal token
        (e.g. ``4.1!51219``) rather than a stable trading symbol, so the
        raw stock_code/symbol cannot be resolved against the Instrument
        Master directly. The underlying is instead resolved through the
        same InstrumentMasterSymbolCanonicalizer used for cash-index ticks,
        keyed off Breeze's ``stock_name``/display-name field, and combined
        with the tick's own expiry/strike/right into a deterministic
        contract symbol. The raw broker token is preserved as broker_symbol.
        """
        display_name = str(item.get("stock_name") or item.get("display_name") or "")
        underlying_source = display_name or broker_quote.symbol
        underlying = self._symbol_canonicalizer.canonicalize(
            underlying_source,
            exchange=broker_quote.exchange,
            broker_code=self._broker.broker_code.value,
        ).symbol
        expiry_date = str(item.get("expiry_date", ""))
        contract_symbol = build_option_contract_symbol(
            underlying, expiry_date, strike_price, option_right
        )
        return CanonicalSymbol(symbol=contract_symbol, broker_symbol=broker_quote.symbol)
