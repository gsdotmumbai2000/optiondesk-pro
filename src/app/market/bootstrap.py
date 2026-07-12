"""Market Master bootstrap and wiring."""

from pathlib import Path

from app.events.event_bus import EventBus
from app.market.cache.market_cache import MarketCache
from app.market.calendar.service import MarketCalendarService
from app.market.expiries.service import ExpiryService
from app.market.holidays.service import HolidayService
from app.market.instrument_master.service import InstrumentService
from app.market.repositories.calendar_repository import CalendarRepository
from app.market.repositories.expiry_repository import ExpiryRepository
from app.market.repositories.holiday_repository import HolidayRepository
from app.market.repositories.instrument_repository import InstrumentRepository
from app.market.sessions.service import TradingSessionService
from app.utils.constants import RESOURCES_DIR


class MarketMasterProvider:
    """Factory for Market Master services."""

    def __init__(
        self,
        data_directory: Path,
        event_bus: EventBus | None = None,
        seed_directory: Path | None = None,
    ) -> None:
        """Initialize repositories and cache."""
        seed = seed_directory or (RESOURCES_DIR / "market")
        self.instrument_repository = InstrumentRepository(data_directory, seed)
        self.holiday_repository = HolidayRepository(seed)
        self.expiry_repository = ExpiryRepository(seed)
        self.calendar_repository = CalendarRepository(seed)
        self.cache = MarketCache(
            self.instrument_repository,
            self.holiday_repository,
            self.expiry_repository,
            self.calendar_repository,
            event_bus,
        )
        self.instrument_service = InstrumentService(self.cache)
        self.calendar_service = MarketCalendarService(self.cache)
        self.expiry_service = ExpiryService(self.cache)
        self.holiday_service = HolidayService(self.cache)
        self.session_service = TradingSessionService(self.cache)

    def shutdown(self) -> None:
        """Close repositories."""
        self.instrument_repository.close()
        self.holiday_repository.close()
        self.expiry_repository.close()
        self.calendar_repository.close()

    def stop(self) -> None:
        """Stop market master services (service registry lifecycle)."""
        self.shutdown()
