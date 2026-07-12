"""Expiry repository port."""

from datetime import date
from typing import Protocol, runtime_checkable

from app.market.expiries.models import ExpiryRecord, ExpiryRule


@runtime_checkable
class IExpiryRepository(Protocol):
    """Persistence port for expiry rules and records."""

    def initialize(self) -> None:
        """Load or connect to storage."""

    def close(self) -> None:
        """Release storage resources."""

    def get_rules(self, underlying: str) -> list[ExpiryRule]:
        """Return expiry rules for an underlying."""

    def get_expiries(
        self,
        underlying: str,
        *,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[ExpiryRecord]:
        """Return expiry records for an underlying."""

    def save_rule(self, rule: ExpiryRule) -> None:
        """Persist an expiry rule."""

    def save_expiry(self, record: ExpiryRecord) -> None:
        """Persist an expiry record."""
