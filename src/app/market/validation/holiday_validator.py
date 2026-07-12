"""Holiday validator."""

from app.exceptions.validation_exception import ValidationException
from app.market.holidays.models import Holiday


class HolidayValidator:
    """Validate holiday records."""

    def validate(self, holiday: Holiday) -> None:
        """Validate a holiday record."""
        if not holiday.exchange.strip():
            raise ValidationException("exchange is required")
        if not holiday.holiday_name.strip():
            raise ValidationException("holiday_name is required")
