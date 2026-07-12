"""Expiry manager."""

from calendar import monthrange
from datetime import date, datetime, time, timedelta

from app.market.enums import ExpiryType, Weekday
from app.market.expiries.models import ExpiryRecord, ExpiryRule
from app.market.holidays.holiday_manager import HolidayManager
from app.market.ports.expiry_repository import IExpiryRepository
from app.market.utils.dte_utils import calculate_dte, calculate_tte


class ExpiryManager:
    """Calculate and validate expiry schedules."""

    def __init__(
        self,
        repository: IExpiryRepository,
        holiday_manager: HolidayManager,
    ) -> None:
        """Initialize expiry manager."""
        self._repository = repository
        self._holiday_manager = holiday_manager

    def get_rules(self, underlying: str) -> list[ExpiryRule]:
        """Return expiry rules for an underlying."""
        return self._repository.get_rules(underlying)

    def nearest_expiry(
        self,
        underlying: str,
        exchange: str,
        *,
        on_date: date,
        expiry_type: ExpiryType = ExpiryType.WEEKLY,
    ) -> ExpiryRecord | None:
        """Return the nearest expiry on or after a date."""
        expiries = self.generate_expiries(
            underlying,
            exchange,
            from_date=on_date,
            to_date=on_date + timedelta(days=90),
            expiry_type=expiry_type,
        )
        if not expiries:
            return None
        return min(expiries, key=lambda item: item.expiry_date)

    def next_expiry(
        self,
        underlying: str,
        exchange: str,
        *,
        after_date: date,
        expiry_type: ExpiryType = ExpiryType.WEEKLY,
    ) -> ExpiryRecord | None:
        """Return the next expiry strictly after a date."""
        expiries = self.generate_expiries(
            underlying,
            exchange,
            from_date=after_date + timedelta(days=1),
            to_date=after_date + timedelta(days=120),
            expiry_type=expiry_type,
        )
        if not expiries:
            return None
        return min(expiries, key=lambda item: item.expiry_date)

    def generate_expiries(
        self,
        underlying: str,
        exchange: str,
        *,
        from_date: date,
        to_date: date,
        expiry_type: ExpiryType,
    ) -> list[ExpiryRecord]:
        """Generate expiry records for a date range."""
        rules = [
            rule
            for rule in self.get_rules(underlying)
            if rule.expiry_type == expiry_type and rule.is_active
        ]
        records: list[ExpiryRecord] = []
        for rule in rules:
            records.extend(self._generate_for_rule(rule, exchange, from_date, to_date))
        records.sort(key=lambda item: item.expiry_date)
        for record in records:
            self._repository.save_expiry(record)
        return records

    def calculate_dte(self, exchange: str, from_date: date, expiry_date: date) -> int:
        """Calculate trading days to expiry."""
        trading_days = self._build_trading_day_set(exchange, from_date, expiry_date)
        return calculate_dte(from_date, expiry_date, trading_days)

    def calculate_tte(
        self,
        exchange: str,
        now: datetime,
        expiry_date: date,
        *,
        market_close: time = time(15, 30),
    ) -> int:
        """Calculate seconds to expiry at market close."""
        return calculate_tte(now, expiry_date, market_close)

    def validate_expiry(self, exchange: str, expiry_date: date) -> bool:
        """Validate that an expiry date is a trading day after holiday shift."""
        shifted = self._holiday_manager.shift_for_holiday(exchange, expiry_date)
        return shifted == expiry_date

    def _generate_for_rule(
        self,
        rule: ExpiryRule,
        exchange: str,
        from_date: date,
        to_date: date,
    ) -> list[ExpiryRecord]:
        """Generate expiries for a single rule."""
        if rule.expiry_type == ExpiryType.WEEKLY:
            return self._weekly_expiries(rule, exchange, from_date, to_date)
        if rule.expiry_type == ExpiryType.MONTHLY:
            return self._monthly_expiries(rule, exchange, from_date, to_date)
        return []

    def _weekly_expiries(
        self,
        rule: ExpiryRule,
        exchange: str,
        from_date: date,
        to_date: date,
    ) -> list[ExpiryRecord]:
        """Generate weekly expiries."""
        if rule.weekday is None:
            return []
        target = self._weekday_to_int(rule.weekday)
        current = from_date
        records: list[ExpiryRecord] = []
        seen: set[date] = set()
        while current <= to_date:
            days_ahead = (target - current.weekday()) % 7
            expiry = current + timedelta(days=days_ahead)
            if expiry > to_date:
                break
            if expiry not in seen:
                records.append(self._build_record(rule, exchange, expiry))
                seen.add(expiry)
            current = expiry + timedelta(days=7)
        return records

    def _monthly_expiries(
        self,
        rule: ExpiryRule,
        exchange: str,
        from_date: date,
        to_date: date,
    ) -> list[ExpiryRecord]:
        """Generate monthly expiries using last weekday rule."""
        if rule.weekday is None:
            return []
        target = self._weekday_to_int(rule.weekday)
        records: list[ExpiryRecord] = []
        year = from_date.year
        month = from_date.month
        while date(year, month, 1) <= to_date:
            last_day = monthrange(year, month)[1]
            expiry = date(year, month, last_day)
            while expiry.weekday() != target:
                expiry -= timedelta(days=1)
            if from_date <= expiry <= to_date:
                records.append(self._build_record(rule, exchange, expiry))
            month += 1
            if month > 12:
                month = 1
                year += 1
        return records

    def _build_record(
        self, rule: ExpiryRule, exchange: str, expiry: date
    ) -> ExpiryRecord:
        """Build an expiry record with holiday shift."""
        shifted = self._holiday_manager.shift_for_holiday(exchange, expiry)
        return ExpiryRecord(
            underlying=rule.underlying,
            expiry_date=shifted,
            expiry_type=rule.expiry_type,
            is_shifted=shifted != expiry,
            original_date=expiry if shifted != expiry else None,
        )

    def _build_trading_day_set(
        self,
        exchange: str,
        from_date: date,
        to_date: date,
    ) -> set[date]:
        """Build a set of trading days in a range."""
        days: set[date] = set()
        current = from_date
        while current <= to_date:
            if self._holiday_manager.is_trading_day(exchange, current):
                days.add(current)
            current += timedelta(days=1)
        return days

    @staticmethod
    def _weekday_to_int(weekday: Weekday) -> int:
        """Map Weekday enum to Python weekday integer."""
        mapping = {
            Weekday.MONDAY: 0,
            Weekday.TUESDAY: 1,
            Weekday.WEDNESDAY: 2,
            Weekday.THURSDAY: 3,
            Weekday.FRIDAY: 4,
            Weekday.SATURDAY: 5,
            Weekday.SUNDAY: 6,
        }
        return mapping[weekday]
