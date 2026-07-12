"""Market cache with lazy loading."""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING

from app.events.event_bus import EventBus
from app.market.events import (CalendarLoadedEvent, ExpiryLoadedEvent,
                               HolidayLoadedEvent, InstrumentLoadedEvent)
from app.market.instrument_master.models import Instrument
from app.market.ports.calendar_repository import ICalendarRepository
from app.market.ports.expiry_repository import IExpiryRepository
from app.market.ports.holiday_repository import IHolidayRepository
from app.market.ports.instrument_repository import IInstrumentRepository

if TYPE_CHECKING:
    from app.market.calendar.market_calendar import MarketCalendar
    from app.market.expiries.expiry_manager import ExpiryManager
    from app.market.holidays.holiday_manager import HolidayManager


class MarketCache:
    """Lazy-loaded cache for market master data."""

    def __init__(
        self,
        instrument_repository: IInstrumentRepository,
        holiday_repository: IHolidayRepository,
        expiry_repository: IExpiryRepository,
        calendar_repository: ICalendarRepository,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize market cache."""
        self._instrument_repository = instrument_repository
        self._holiday_repository = holiday_repository
        self._expiry_repository = expiry_repository
        self._calendar_repository = calendar_repository
        self._event_bus = event_bus
        self._lock = RLock()
        self._instruments_loaded = False
        self._holidays_loaded = False
        self._expiries_loaded = False
        self._calendar_loaded = False
        self._holiday_manager: HolidayManager | None = None
        self._expiry_manager: ExpiryManager | None = None
        self._market_calendar: MarketCalendar | None = None

    @property
    def holiday_manager(self) -> HolidayManager:
        """Return holiday manager with lazy initialization."""
        with self._lock:
            self._ensure_holidays_loaded()
            assert self._holiday_manager is not None
            return self._holiday_manager

    @property
    def expiry_manager(self) -> ExpiryManager:
        """Return expiry manager with lazy initialization."""
        with self._lock:
            self._ensure_expiries_loaded()
            assert self._expiry_manager is not None
            return self._expiry_manager

    @property
    def market_calendar(self) -> MarketCalendar:
        """Return market calendar with lazy initialization."""
        with self._lock:
            self._ensure_calendar_loaded()
            assert self._market_calendar is not None
            return self._market_calendar

    def get_instruments(self) -> list[Instrument]:
        """Return all instruments from cache."""
        with self._lock:
            self._ensure_instruments_loaded()
            return self._instrument_repository.get_all()

    def find_by_symbol(self, trading_symbol: str) -> list[Instrument]:
        """Find instruments by trading symbol."""
        with self._lock:
            self._ensure_instruments_loaded()
            return self._instrument_repository.get_by_symbol(trading_symbol)

    def find_by_exchange(self, exchange: str) -> list[Instrument]:
        """Find instruments by exchange."""
        with self._lock:
            self._ensure_instruments_loaded()
            return self._instrument_repository.get_by_exchange(exchange)

    def find_by_underlying(self, underlying: str) -> list[Instrument]:
        """Find instruments by underlying."""
        with self._lock:
            self._ensure_instruments_loaded()
            return self._instrument_repository.get_by_underlying(underlying)

    def find_by_instrument_type(self, instrument_type: str) -> list[Instrument]:
        """Find instruments by type."""
        with self._lock:
            self._ensure_instruments_loaded()
            return self._instrument_repository.get_by_instrument_type(instrument_type)

    def get_instrument_by_id(self, instrument_id: str) -> Instrument | None:
        """Return instrument by id."""
        with self._lock:
            self._ensure_instruments_loaded()
            return self._instrument_repository.get_by_id(instrument_id)

    def save_instrument(self, instrument: Instrument) -> None:
        """Save an instrument to the repository."""
        with self._lock:
            self._ensure_instruments_loaded()
            self._instrument_repository.save(instrument)

    def invalidate(self) -> None:
        """Invalidate all cached data."""
        with self._lock:
            self._instruments_loaded = False
            self._holidays_loaded = False
            self._expiries_loaded = False
            self._calendar_loaded = False
            self._holiday_manager = None
            self._expiry_manager = None
            self._market_calendar = None

    def _ensure_instruments_loaded(self) -> None:
        """Load instruments if not already loaded."""
        if self._instruments_loaded:
            return
        self._instrument_repository.initialize()
        count = len(self._instrument_repository.get_all())
        self._instruments_loaded = True
        self._publish(InstrumentLoadedEvent(payload={"count": count}))

    def _ensure_holidays_loaded(self) -> None:
        """Load holidays if not already loaded."""
        if self._holidays_loaded:
            return
        from app.market.holidays.holiday_manager import HolidayManager

        self._holiday_repository.initialize()
        self._holiday_manager = HolidayManager(self._holiday_repository)
        self._holidays_loaded = True
        self._publish(HolidayLoadedEvent())

    def _ensure_expiries_loaded(self) -> None:
        """Load expiry data if not already loaded."""
        if self._expiries_loaded:
            return
        from app.market.expiries.expiry_manager import ExpiryManager

        self._ensure_holidays_loaded()
        self._expiry_repository.initialize()
        assert self._holiday_manager is not None
        self._expiry_manager = ExpiryManager(
            self._expiry_repository, self._holiday_manager
        )
        self._expiries_loaded = True
        self._publish(ExpiryLoadedEvent())

    def _ensure_calendar_loaded(self) -> None:
        """Load calendar data if not already loaded."""
        if self._calendar_loaded:
            return
        from app.market.calendar.market_calendar import MarketCalendar

        self._ensure_holidays_loaded()
        self._calendar_repository.initialize()
        assert self._holiday_manager is not None
        self._market_calendar = MarketCalendar(
            self._calendar_repository, self._holiday_manager
        )
        self._calendar_loaded = True
        self._publish(CalendarLoadedEvent())

    def _publish(
        self,
        event: (
            InstrumentLoadedEvent
            | HolidayLoadedEvent
            | ExpiryLoadedEvent
            | CalendarLoadedEvent
        ),
    ) -> None:
        """Publish a market event if bus is configured."""
        if self._event_bus is not None:
            self._event_bus.publish(event)
