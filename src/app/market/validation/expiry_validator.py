"""Expiry validator."""

from datetime import date

from app.exceptions.validation_exception import ValidationException
from app.market.expiries.models import ExpiryRecord


class ExpiryValidator:
    """Validate expiry records."""

    def validate(
        self, record: ExpiryRecord, *, reference_date: date | None = None
    ) -> None:
        """Validate an expiry record."""
        if not record.underlying.strip():
            raise ValidationException("underlying is required")
        if reference_date and record.expiry_date < reference_date:
            raise ValidationException("expiry_date cannot be before reference date")
