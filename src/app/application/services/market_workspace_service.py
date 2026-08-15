"""Market workspace service."""

from datetime import date, datetime, timezone
from decimal import Decimal

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult, WorkspaceView
from app.application.ports.live_analytics_port import LiveAnalyticsPort
from app.application.registry.engine_registry import EngineRegistry
from app.application.services.live_analytics_support import LiveAnalyticsSupport
from app.application.session.session_manager import SessionManager
from app.brokers.shared.enums import ProductType
from app.logging.logging_manager import get_logger
from app.market.enums import ExchangeCode, ExpiryType
from app.market_data.models.snapshot import MarketSnapshot
from app.market_data.services.market_data_service import MarketDataService

logger = get_logger(__name__)

_STRIKE_WINDOW_RADIUS = 10


class MarketWorkspaceService(LiveAnalyticsSupport):
    """Market data workspace API for UI."""

    def __init__(
        self,
        engines: EngineRegistry,
        sessions: SessionManager,
        cache: WorkspaceCache,
        market_data: MarketDataService | None = None,
        live_analytics: LiveAnalyticsPort | None = None,
    ) -> None:
        """Initialize service."""
        super().__init__(live_analytics)
        self._engines = engines
        self._sessions = sessions
        self._cache = cache
        self._market_data = market_data or self._resolve_market_data()
        self._watchlists: dict[str, tuple[str, ...]] = {}

    def refresh_market(self, session_id: str) -> WorkspaceOperationResult:
        """Refresh market data via market data service."""
        if self._market_data is None:
            return WorkspaceOperationResult(
                False,
                WorkspaceType.MARKET,
                "Market data engine not configured",
            )
        status = self._market_data.market_status()
        self._cache.put_data(
            f"{session_id}:market",
            {
                "status": status.status.value,
                "exchange": status.exchange,
                "tick_count": self._market_data.tick_count(),
            },
        )
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            f"Market status: {status.status.value}",
        )

    def subscribe_symbol(
        self,
        session_id: str,
        symbol: str,
        exchange: str = "NSE",
        *,
        product_type: str = "CASH",
    ) -> WorkspaceOperationResult:
        """Queue symbol for subscription (activates when broker connects)."""
        if self._market_data is None:
            return WorkspaceOperationResult(False, WorkspaceType.MARKET, "No market data")
        self._market_data.subscribe(
            symbol,
            exchange,
            product_type=ProductType(product_type),
        )
        pending = self._market_data.connection_status().value != "Connected"
        message = f"Queued {symbol}" if pending else f"Subscribed to {symbol}"
        return WorkspaceOperationResult(
            True, WorkspaceType.MARKET, message, {"symbol": symbol}
        )

    def latest_quote(
        self,
        session_id: str,
        symbol: str,
        exchange: str = "NSE",
    ) -> WorkspaceOperationResult:
        """Return latest tick for symbol."""
        if self._market_data is None:
            return WorkspaceOperationResult(False, WorkspaceType.MARKET, "No market data")
        tick = self._market_data.latest_tick(symbol, exchange)
        payload = tick.model_dump(mode="json") if tick is not None else {}
        return WorkspaceOperationResult(
            tick is not None,
            WorkspaceType.MARKET,
            f"Latest {symbol}",
            payload,
        )

    def market_status(self, session_id: str) -> WorkspaceOperationResult:
        """Return live market status."""
        if self._market_data is None:
            return WorkspaceOperationResult(False, WorkspaceType.MARKET, "No market data")
        snap = self._market_data.market_status()
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            snap.status.value,
            {
                "status": snap.status.value,
                "exchange": snap.exchange,
                "connection": self._market_data.connection_status().value,
                "last_tick": str(self._market_data.last_tick_time() or ""),
            },
        )

    def watchlist(self, session_id: str, symbols: tuple[str, ...]) -> WorkspaceOperationResult:
        """Set watchlist symbols in memory (subscriptions remain pending)."""
        self._watchlists[session_id] = symbols
        self._cache.put_data(f"{session_id}:watchlist", symbols)
        if self._market_data is not None:
            self._market_data.load_watchlist(symbols)
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            f"Watchlist loaded ({len(symbols)} symbols, subscriptions pending)",
            symbols,
        )

    def market_overview(self, session_id: str) -> WorkspaceOperationResult:
        """Return market overview from live service."""
        cached = self._cache.get_data(f"{session_id}:market")
        status = self.market_status(session_id)
        payload = status.data or {}
        if cached:
            payload = {**cached, **payload}
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            "Market overview",
            payload,
        )

    def option_chain(
        self,
        session_id: str,
        symbol: str,
        *,
        exchange: str = "NSE",
        expiry_date: str = "",
    ) -> WorkspaceOperationResult:
        """Return live option chain analytics."""
        chain = self.live_option_chain(symbol, exchange, expiry_date)
        payload = chain.model_dump(mode="json") if chain is not None else {}
        if chain is not None:
            self._cache.put_data(f"{session_id}:chain:{symbol}", payload)
        return WorkspaceOperationResult(
            chain is not None,
            WorkspaceType.MARKET,
            f"Option chain for {symbol}",
            payload,
        )

    def initial_option_chain(
        self,
        session_id: str,
        underlying: str = "NIFTY",
        *,
        exchange: str = "NFO",
    ) -> WorkspaceOperationResult:
        """Fetch an initial REST option-chain snapshot for the ATM window.

        Resolves the nearest weekly expiry and ATM-centered strike window
        via the Instrument/Expiry Master (never hard-coded), fetches the
        chain through the existing MarketDataService/broker REST path
        (which also populates the existing market-data chain cache), and
        subscribes live CALL+PUT feeds for the displayed window so
        subsequent ticks flow through the existing live pipeline.

        This performs a broker REST call and ~2N subscribe calls; callers
        must invoke it off the Qt UI thread.
        """
        logger.debug(
            "initial_option_chain: entering underlying={underlying} exchange={exchange}",
            underlying=underlying,
            exchange=exchange,
        )
        if self._market_data is None:
            return WorkspaceOperationResult(False, WorkspaceType.MARKET, "No market data")

        instrument_service = self._engines.market_master.instrument_service
        expiry_service = self._engines.market_master.expiry_service
        expiry_record = expiry_service.nearest_expiry(
            underlying, ExchangeCode.NSEFO.value, on_date=date.today()
        )
        if expiry_record is None:
            return WorkspaceOperationResult(
                False, WorkspaceType.MARKET, f"No expiry available for {underlying}"
            )
        expiry_date = expiry_record.expiry_date.strftime("%d-%b-%Y")
        logger.debug("initial_option_chain: expiry resolved expiry_date={expiry_date}", expiry_date=expiry_date)

        future_expiry_record = expiry_service.nearest_expiry(
            underlying,
            ExchangeCode.NSEFO.value,
            on_date=date.today(),
            expiry_type=ExpiryType.MONTHLY,
        )
        if future_expiry_record is not None:
            self._subscribe_future(
                underlying,
                exchange,
                future_expiry_record.expiry_date.strftime("%d-%b-%Y"),
            )

        logger.debug("initial_option_chain: calling market_data.get_option_chain")
        chain = self._market_data.get_option_chain(underlying, exchange, expiry_date)
        logger.debug("initial_option_chain: market_data.get_option_chain returned")

        spot = chain.spot_price
        if spot is None:
            tick = self._market_data.latest_tick(underlying, "NSE")
            spot = tick.ltp if tick is not None else None

        atm: Decimal | None = None
        window: list[Decimal] = []
        if spot is not None:
            try:
                interval = instrument_service.get_strike_interval(underlying)
                atm = instrument_service.atm_strike(underlying, spot)
            except LookupError:
                atm = None
            if atm is not None and interval > 0:
                window = [
                    atm + (interval * offset)
                    for offset in range(-_STRIKE_WINDOW_RADIUS, _STRIKE_WINDOW_RADIUS + 1)
                ]
        logger.debug("initial_option_chain: ATM strike resolved atm={atm}", atm=atm)

        strikes_by_price = {strike.strike_price: strike for strike in chain.strikes}
        windowed = [strikes_by_price[price] for price in window if price in strikes_by_price]
        for strike in windowed:
            strike.is_atm = atm is not None and strike.strike_price == atm

        if window:
            logger.debug(
                "initial_option_chain: subscribing option window strike_count={count}",
                count=len(window),
            )
            self._subscribe_option_window(underlying, exchange, expiry_date, window)
            logger.debug("initial_option_chain: option window subscribed")

        payload = {
            "underlying": underlying,
            "exchange": exchange,
            "expiry_date": expiry_date,
            "spot_price": str(spot) if spot is not None else None,
            "atm_strike": str(atm) if atm is not None else None,
            "strikes": [strike.model_dump(mode="json") for strike in windowed],
        }
        self._cache.put_data(f"{session_id}:chain:{underlying}", payload)
        logger.debug(
            "initial_option_chain: result returned strike_count={count}",
            count=len(windowed),
        )
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            f"Option chain for {underlying} {expiry_date} ({len(windowed)} strikes)",
            payload,
        )

    def _subscribe_future(self, underlying: str, exchange: str, expiry_date: str) -> None:
        """Subscribe the live futures feed for the underlying's futures expiry.

        `expiry_date` here is the *monthly* futures expiry, resolved
        separately from the option chain's weekly `expiry_date` above --
        NIFTY-family futures and options do not share an expiry cycle, so
        reusing the weekly value made every futures subscription request an
        expiry Breeze has no contract for (Task 10).

        Calculation contexts require a future quote (MarketSnapshotBuilder.future
        -> LiveMarketQueryAdapter.get_future) independent of the option strike
        window below, so this must not be gated on `window` being non-empty.
        Deduplication is handled by SubscriptionService's own identity key
        (exchange:symbol:product_type:expiry:strike:right), so repeated calls
        for the same underlying/exchange/expiry are safe no-ops at the broker.

        A broker-level subscribe failure (e.g. no futures contract exists at
        this expiry) must not abort the rest of initial_option_chain() — the
        REST chain fetch and option-window subscription below have no
        dependency on this succeeding, and SubscriptionService.subscribe()
        does not itself guard against the broker call raising.
        """
        if self._market_data is None:
            return
        try:
            self._market_data.subscribe(
                underlying,
                exchange,
                product_type=ProductType.FUTURES,
                expiry_date=expiry_date,
            )
        except Exception as error:
            logger.warning(
                "initial_option_chain: future subscription failed for "
                "{underlying}@{exchange} expiry_date={expiry_date}: {error}",
                underlying=underlying,
                exchange=exchange,
                expiry_date=expiry_date,
                error=error,
            )

    def _subscribe_option_window(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
        strikes: list[Decimal],
    ) -> None:
        """Subscribe live CALL and PUT feeds for every strike in the window."""
        if self._market_data is None:
            return
        for strike in strikes:
            for right in ("CALL", "PUT"):
                self._market_data.subscribe(
                    underlying,
                    exchange,
                    product_type=ProductType.OPTIONS,
                    expiry_date=expiry_date,
                    strike_price=str(strike),
                    option_right=right,
                )

    def live_analytics(
        self,
        session_id: str,
        symbol: str,
        *,
        exchange: str = "NSE",
        expiry_date: str = "",
    ) -> WorkspaceOperationResult:
        """Return live analytics snapshot for symbol."""
        snapshot = self.live_analytics_snapshot(symbol, exchange, expiry_date)
        payload = {}
        if snapshot is not None:
            payload = {
                "underlying": snapshot.underlying,
                "exchange": snapshot.exchange,
                "expiry_date": snapshot.expiry_date,
                "calculation_timestamp": str(snapshot.calculation_timestamp or ""),
            }
            self._cache.put_data(f"{session_id}:analytics:{symbol}", payload)
        return WorkspaceOperationResult(
            snapshot is not None,
            WorkspaceType.MARKET,
            f"Live analytics for {symbol}",
            payload,
        )

    def market_scanner(self, session_id: str) -> WorkspaceOperationResult:
        """Return scanner results (framework)."""
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            "Market scanner results",
            self._cache.get_data(f"{session_id}:scanner"),
        )

    def volatility_dashboard(self, session_id: str) -> WorkspaceOperationResult:
        """Return volatility dashboard data (framework)."""
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            "Volatility dashboard",
            self._cache.get_data(f"{session_id}:volatility"),
        )

    def cache_snapshot(self, session_id: str, snapshot: MarketSnapshot) -> None:
        """Cache market snapshot for UI queries."""
        self._cache.put_data(f"{session_id}:snapshot", snapshot)

    def view(self, session_id: str) -> WorkspaceView:
        """Return market workspace view."""
        symbols = self._watchlists.get(session_id, ())
        return WorkspaceView(
            workspace=WorkspaceType.MARKET,
            title="Market Workspace",
            summary=f"Watchlist: {len(symbols)} symbols",
            entity_id="",
            updated_at=datetime.now(timezone.utc),
        )

    def _resolve_market_data(self) -> MarketDataService | None:
        provider = self._engines.market_data
        return provider.service if provider is not None else None
