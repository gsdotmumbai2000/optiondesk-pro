"""Calculation context factory."""

from datetime import date, datetime
from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.events import (
    CalculationContextCreatedEvent,
    CalculationContextInvalidEvent,
)
from app.calculation.exceptions import InvalidContextException
from app.calculation.factory.snapshot_builder import MarketSnapshotBuilder
from app.calculation.models.configuration import CalculationConfiguration
from app.calculation.models.market_session import MarketSession
from app.calculation.models.snapshots import (
    FutureQuoteSnapshot,
    OptionChainSnapshot,
    SpotQuoteSnapshot,
)
from app.calculation.providers.dividend_provider import DividendProvider
from app.calculation.providers.expiry_provider import ExpiryProvider
from app.calculation.providers.interest_rate_provider import InterestRateProvider
from app.calculation.providers.market_status_provider import MarketStatusProvider
from app.calculation.providers.ports import IInstrumentSpecificationPort, IMarketDataQueryPort
from app.calculation.providers.time_provider import TimeProvider
from app.calculation.providers.underlying_provider import (
    UnderlyingInfo,
    UnderlyingProvider,
    cash_exchange_for,
)
from app.calculation.providers.volatility_provider import VolatilityProvider
from app.calculation.utilities.normalize_utils import normalize_price
from app.calculation.utilities.strike_utils import atm_strike
from app.calculation.validation.context_validator import ContextValidator
from app.events.event_bus import EventBus


class CalculationContextFactory:
    """Build immutable calculation contexts from providers."""

    def __init__(
        self,
        market_data: IMarketDataQueryPort,
        instruments: IInstrumentSpecificationPort,
        expiry_provider: ExpiryProvider,
        interest_provider: InterestRateProvider,
        dividend_provider: DividendProvider,
        volatility_provider: VolatilityProvider,
        market_status_provider: MarketStatusProvider,
        time_provider: TimeProvider | None = None,
        validator: ContextValidator | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize factory dependencies."""
        self._snapshots = MarketSnapshotBuilder(market_data)
        self._instruments = instruments
        self._expiry = expiry_provider
        self._interest = interest_provider
        self._dividend = dividend_provider
        self._volatility = volatility_provider
        self._market_status = market_status_provider
        self._time = time_provider or TimeProvider()
        self._validator = validator or ContextValidator()
        self._event_bus = event_bus
        self._underlying = UnderlyingProvider()

    def build(
        self,
        underlying: str,
        exchange: str,
        expiry: str,
        *,
        configuration: CalculationConfiguration | None = None,
    ) -> CalculationContext:
        """Create a validated calculation context."""
        try:
            context = self._assemble(underlying, exchange, expiry, configuration)
            self._validator.validate(context)
            self._publish(
                CalculationContextCreatedEvent(payload={"underlying": underlying})
            )
            return context
        except InvalidContextException as error:
            self._publish(
                CalculationContextInvalidEvent(payload={"reason": str(error)})
            )
            raise

    def _assemble(
        self,
        underlying: str,
        exchange: str,
        expiry: str,
        configuration: CalculationConfiguration | None,
    ) -> CalculationContext:
        info = self._underlying.resolve(underlying, exchange)
        now = self._time.now()
        trade_date = self._time.trade_date(now)
        expiry_date = self._expiry.parse_expiry(expiry)
        spot = self._snapshots.spot(info.underlying_symbol, cash_exchange_for(info.exchange))
        future_expiry = self._resolve_future_expiry(
            info.underlying_symbol, info.exchange, trade_date, fallback=expiry
        )
        future = self._snapshots.future(info.underlying_symbol, info.exchange, future_expiry)
        chain = self._snapshots.option_chain(info.underlying_symbol, info.exchange, expiry)
        session = self._market_status.session(info.exchange, now)
        return self._build_context(
            info=info,
            expiry_date=expiry_date,
            now=now,
            trade_date=trade_date,
            spot=spot,
            future=future,
            chain=chain,
            session=session,
            configuration=configuration,
        )

    def _resolve_future_expiry(
        self, underlying: str, exchange: str, trade_date: date, *, fallback: str
    ) -> str:
        """Resolve the futures contract's own (monthly) expiry, independent
        of the option chain's (weekly) expiry passed into this context.

        NIFTY-family futures expire monthly while their options expire
        weekly, so the two are not the same contract date and must not
        share a lookup key (see Task 9/10: get_future() silently missed
        every live futures tick because it reused the weekly expiry).
        Falls back to the option expiry if no monthly expiry is resolvable
        for this underlying (e.g. no futures market for it), matching prior
        behavior rather than failing the whole context.
        """
        monthly = self._expiry.nearest_monthly_expiry(underlying, exchange, trade_date)
        if monthly is None:
            return fallback
        return monthly.strftime("%d-%b-%Y")

    def _build_context(
        self,
        *,
        info: UnderlyingInfo,
        expiry_date: date,
        now: datetime,
        trade_date: date,
        spot: SpotQuoteSnapshot,
        future: FutureQuoteSnapshot,
        chain: OptionChainSnapshot,
        session: MarketSession,
        configuration: CalculationConfiguration | None,
    ) -> CalculationContext:
        strike_interval = self._instruments.get_strike_interval(info.underlying)
        spot_price = normalize_price(spot.ltp)
        atm_value = chain.atm_strike or atm_strike(spot_price, strike_interval)
        atm_iv = MarketSnapshotBuilder.atm_implied_volatility(chain)
        vol_provider = self._volatility.from_option_chain(atm_iv)
        dte = self._expiry.days_to_expiry(info.exchange, trade_date, expiry_date)
        tte = self._expiry.time_to_expiry(info.exchange, now, expiry_date)
        return CalculationContext(
            underlying=info.underlying,
            spot_price=spot_price,
            future_price=normalize_price(future.ltp),
            underlying_symbol=info.underlying_symbol,
            exchange=info.exchange,
            expiry=expiry_date,
            current_time=now,
            trade_date=trade_date,
            market_status=self._market_status.status_label(info.exchange, now),
            interest_rate=self._interest.interest_rate(),
            dividend_yield=self._dividend.dividend_yield(),
            risk_free_rate=self._interest.risk_free_rate(),
            volatility=vol_provider.volatility(),
            historical_volatility=vol_provider.historical_volatility(),
            implied_volatility=vol_provider.implied_volatility(),
            days_to_expiry=dte,
            time_to_expiry=tte,
            atm_strike=normalize_price(Decimal(str(atm_value))),
            lot_size=self._instruments.get_lot_size(info.underlying),
            tick_size=self._instruments.get_tick_size(info.underlying),
            strike_interval=strike_interval,
            currency=info.currency,
            market_session=session,
            option_chain_snapshot=chain,
            future_quote=future,
            spot_quote=spot,
            configuration=configuration or CalculationConfiguration(),
            calculation_timestamp=now,
        )

    def _publish(self, event: object) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)
