"""Production Breeze broker adapter."""

from collections.abc import Callable
from datetime import datetime
from threading import RLock

from app.brokers.breeze.authentication import BreezeAuthentication
from app.brokers.breeze.authentication_service import BreezeAuthenticationService
from app.brokers.breeze.client import resolve_client_factory
from app.brokers.breeze.configuration_provider import BreezeConfigurationProvider
from app.brokers.breeze.historical import BreezeHistorical
from app.brokers.breeze.margin import BreezeMargin
from app.brokers.breeze.market_data import BreezeMarketData
from app.brokers.breeze.option_chain import BreezeOptionChain
from app.brokers.breeze.portfolio import BreezePortfolio
from app.brokers.breeze.session_manager import BreezeSessionManager
from app.brokers.breeze.session_store import BreezeSessionStore
from app.brokers.breeze.trading import BreezeTrading
from app.brokers.breeze.websocket import BreezeWebSocket
from app.brokers.broker_interface.interface import BrokerInterface
from app.brokers.events import (OrderCancelledEvent, OrderModifiedEvent,
                                OrderPlacedEvent, PortfolioUpdatedEvent)
from app.brokers.shared.enums import BrokerCode, ConnectionState
from app.brokers.shared.exceptions import BrokerConnectionException
from app.brokers.shared.models import (BrokerHealth, BrokerProfile, Funds,
                                       HistoricalBar, HistoricalRequest,
                                       Holding, Margins, OptionChain,
                                       OptionChainRequest, Order,
                                       OrderModification, OrderRequest,
                                       Position, Quote, QuoteSubscription)
from app.config.models.app_config import BrokerConfig
from app.events.application_events import ApplicationEvent
from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger
from app.security.credential_manager import CredentialManager

logger = get_logger(__name__)


class BreezeBrokerAdapter(BrokerInterface):
    """Breeze broker adapter implementing BrokerInterface."""

    def __init__(
        self,
        config: BrokerConfig,
        credential_manager: CredentialManager,
        event_bus: EventBus | None = None,
        *,
        client_factory: Callable[[str], object] | None = None,
        session_store: BreezeSessionStore | None = None,
    ) -> None:
        """Initialize Breeze broker adapter."""
        self._config = config
        self._event_bus = event_bus
        self._lock = RLock()
        self._state = ConnectionState.DISCONNECTED
        self._config_provider = BreezeConfigurationProvider(config, credential_manager)
        api_key = self._config_provider.get_api_key() or ""
        factory = resolve_client_factory(client_factory)
        self._client = factory(api_key)
        self._auth = BreezeAuthentication(
            self._client, credential_manager, config.account_name
        )
        self._auth_service = BreezeAuthenticationService(
            self._auth,
            self._config_provider,
            session_store,
            event_bus,
        )
        self._session = BreezeSessionManager(
            self._auth, self._auth_service, config, session_store
        )
        self._market_data = BreezeMarketData(self._client)
        self._historical = BreezeHistorical(self._client)
        self._trading = BreezeTrading(self._client)
        self._portfolio = BreezePortfolio(self._client, BrokerCode.BREEZE.value)
        self._margin = BreezeMargin(self._client)
        self._option_chain = BreezeOptionChain(self._client)
        self._websocket = BreezeWebSocket(self._client, event_bus)

    @property
    def broker_code(self) -> BrokerCode:
        return BrokerCode.BREEZE

    @property
    def connection_state(self) -> ConnectionState:
        with self._lock:
            return self._state

    @property
    def auth_service(self) -> BreezeAuthenticationService:
        """Return authentication service."""
        return self._auth_service

    @property
    def config_provider(self) -> BreezeConfigurationProvider:
        """Return configuration provider."""
        return self._config_provider

    def connect(self) -> None:
        """Initialize Breeze client connection."""
        with self._lock:
            self._state = ConnectionState.CONNECTING
            if self._config.auto_login and self._config_provider.has_credentials():
                self._state = ConnectionState.AUTHENTICATING
            elif self._auth_service.restore_session():
                self._session.mark_authenticated()
                self._state = ConnectionState.CONNECTED
            else:
                self._state = ConnectionState.DISCONNECTED
            if self._config.websocket_enabled and self._state == ConnectionState.CONNECTED:
                self._websocket.connect()

    def disconnect(self) -> None:
        """Disconnect websocket and clear state."""
        with self._lock:
            self._websocket.disconnect()
            self._state = ConnectionState.DISCONNECTED

    def authenticate(self) -> None:
        """Authenticate with Breeze.

        AuthenticationSucceededEvent is published only after the session is
        marked authenticated and broker state is CONNECTED, so subscribers
        (e.g. MarketViewModel triggering the option-chain load) never see
        the event before the session is actually usable for API calls.

        The websocket connect() call must happen before publish_authenticated():
        subscribers of AuthenticationSucceededEvent are invoked synchronously
        and include the default-subscription activation path, which calls the
        broker's subscribe_quotes() immediately. If the underlying Breeze SDK
        websocket has not connected yet at that point, its subscribe_feeds()
        silently no-ops (it only acts once its socket handler exists) without
        raising or returning an error string, so the subscription is marked
        active locally while never having reached the server.
        """
        with self._lock:
            self._auth_service.login()
            self._session.mark_authenticated()
            logger.debug("Breeze session marked authenticated")
            self._state = ConnectionState.CONNECTED
            logger.debug("Broker state set to CONNECTED")
            if self._config.websocket_enabled:
                self._websocket.connect()
            self._auth_service.publish_authenticated()

    def refresh_session(self) -> None:
        """Refresh Breeze session."""
        with self._lock:
            self._session.refresh_session()

    def logout(self) -> None:
        """Logout and disconnect."""
        with self._lock:
            self._session.logout()
            self.disconnect()

    def is_connected(self) -> bool:
        with self._lock:
            return self._state == ConnectionState.CONNECTED

    def get_profile(self) -> BrokerProfile:
        self._ensure_session()
        return self._portfolio.get_profile(self._auth.session_token)

    def get_funds(self) -> Funds:
        self._ensure_session()
        funds = self._portfolio.get_funds()
        self._publish_portfolio({"type": "funds"})
        return funds

    def get_holdings(self) -> list[Holding]:
        self._ensure_session()
        holdings = self._portfolio.get_holdings()
        self._publish_portfolio({"type": "holdings", "count": len(holdings)})
        return holdings

    def get_positions(self) -> list[Position]:
        self._ensure_session()
        positions = self._portfolio.get_positions()
        self._publish_portfolio({"type": "positions", "count": len(positions)})
        return positions

    def get_orders(
        self,
        exchange: str,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[Order]:
        self._ensure_session()
        return self._trading.get_orders(exchange, from_date=from_date, to_date=to_date)

    def place_order(self, request: OrderRequest) -> Order:
        self._ensure_session()
        order = self._trading.place_order(request)
        self._publish(OrderPlacedEvent(payload={"order_id": order.order_id}))
        return order

    def modify_order(self, modification: OrderModification) -> Order:
        self._ensure_session()
        order = self._trading.modify_order(modification)
        self._publish(OrderModifiedEvent(payload={"order_id": order.order_id}))
        return order

    def cancel_order(self, exchange: str, order_id: str) -> Order:
        self._ensure_session()
        order = self._trading.cancel_order(exchange, order_id)
        self._publish(OrderCancelledEvent(payload={"order_id": order_id}))
        return order

    def get_quotes(
        self,
        symbol: str,
        exchange: str,
        *,
        expiry_date: str = "",
        product_type: str = "",
        option_right: str = "",
        strike_price: str = "",
    ) -> Quote:
        self._ensure_session()
        return self._market_data.get_quotes(
            symbol,
            exchange,
            expiry_date=expiry_date,
            product_type=product_type,
            option_right=option_right,
            strike_price=strike_price,
        )

    def get_option_chain(self, request: OptionChainRequest) -> OptionChain:
        logger.debug("BreezeBrokerAdapter.get_option_chain: ensuring session")
        self._ensure_session()
        logger.debug("BreezeBrokerAdapter.get_option_chain: session ensured, calling BreezeOptionChain")
        chain = self._option_chain.get_option_chain(request)
        logger.debug("BreezeBrokerAdapter.get_option_chain: BreezeOptionChain returned")
        return chain

    def get_historical_data(self, request: HistoricalRequest) -> list[HistoricalBar]:
        self._ensure_session()
        return self._historical.get_historical_data(request)

    def subscribe_quotes(self, subscription: QuoteSubscription) -> None:
        self._ensure_session()
        self._websocket.subscribe_quotes(subscription)

    def unsubscribe_quotes(self, subscription: QuoteSubscription) -> None:
        self._websocket.unsubscribe_quotes(subscription)

    def subscribe_option_chain(self, request: OptionChainRequest) -> None:
        self._ensure_session()
        self._websocket.subscribe_option_chain(request)

    def unsubscribe_option_chain(self, request: OptionChainRequest) -> None:
        self._websocket.unsubscribe_option_chain(request)

    def download_instrument_master(self) -> list[dict[str, str]]:
        self._ensure_session()
        return self._client.get_stock_script_list()

    def calculate_margin(
        self, positions: list[OrderRequest], exchange_code: str
    ) -> Margins:
        self._ensure_session()
        return self._margin.calculate_margin(positions, exchange_code)

    def health(self) -> BrokerHealth:
        return BrokerHealth(
            broker_code=BrokerCode.BREEZE.value,
            connection_state=self._state,
            is_session_valid=self._session.is_session_valid(),
            websocket_connected=self._websocket.is_connected,
            message="ok" if self.is_connected() else "disconnected",
        )

    def _ensure_session(self) -> None:
        """Validate session before API calls."""
        if not self._session.is_session_valid():
            raise BrokerConnectionException("Breeze session is not valid")

    def _publish(self, event: ApplicationEvent) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)

    def _publish_portfolio(self, payload: dict[str, object]) -> None:
        self._publish(PortfolioUpdatedEvent(payload=payload))
