"""Holiday repository."""

from datetime import date
from pathlib import Path

from app.logging.logging_manager import get_logger
from app.market.holidays.models import Holiday, SpecialSession
from app.market.repositories.data_loader import MarketDataLoader

logger = get_logger(__name__)

DEFAULT_HOLIDAYS_2026 = [
    Holiday(
        exchange="NSE", holiday_date=date(2026, 1, 26), holiday_name="Republic Day"
    ),
    Holiday(exchange="NSE", holiday_date=date(2026, 3, 3), holiday_name="Holi"),
    Holiday(
        exchange="NSE", holiday_date=date(2026, 8, 15), holiday_name="Independence Day"
    ),
    Holiday(
        exchange="NSE", holiday_date=date(2026, 10, 2), holiday_name="Gandhi Jayanti"
    ),
    Holiday(exchange="NSE", holiday_date=date(2026, 11, 9), holiday_name="Diwali"),
]


class HolidayRepository:
    """In-memory holiday repository with file loading."""

    def __init__(self, seed_directory: Path | None = None) -> None:
        """Initialize repository."""
        self._seed_directory = seed_directory
        self._holidays: list[Holiday] = []
        self._sessions: list[SpecialSession] = []

    def initialize(self) -> None:
        """Load holidays and special sessions."""
        self._holidays = list(DEFAULT_HOLIDAYS_2026)
        self._sessions = []
        self._load_seed_files()
        logger.info(
            "Holiday repository loaded {count} holidays", count=len(self._holidays)
        )

    def close(self) -> None:
        """Clear in-memory data."""
        self._holidays.clear()
        self._sessions.clear()

    def get_holidays(self, exchange: str) -> list[Holiday]:
        """Return holidays for an exchange."""
        code = exchange.upper()
        return [item for item in self._holidays if item.exchange.upper() == code]

    def get_holiday_on(self, exchange: str, on_date: date) -> Holiday | None:
        """Return holiday on a date if present."""
        for holiday in self.get_holidays(exchange):
            if holiday.holiday_date == on_date:
                return holiday
        return None

    def get_special_sessions(self, exchange: str) -> list[SpecialSession]:
        """Return special sessions."""
        code = exchange.upper()
        return [item for item in self._sessions if item.exchange.upper() == code]

    def save_holiday(self, holiday: Holiday) -> None:
        """Persist a holiday in memory."""
        self._holidays = [
            item for item in self._holidays if item.holiday_date != holiday.holiday_date
        ]
        self._holidays.append(holiday)

    def _load_seed_files(self) -> None:
        """Load holidays from seed directory."""
        if self._seed_directory is None:
            return
        loader = MarketDataLoader()
        for path in sorted(self._seed_directory.glob("holidays.*")):
            for record in loader.load_records(path):
                self._holidays.append(Holiday.model_validate(record))
