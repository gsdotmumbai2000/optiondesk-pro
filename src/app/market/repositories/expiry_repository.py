"""Expiry repository."""

from datetime import date
from pathlib import Path

from app.logging.logging_manager import get_logger
from app.market.enums import ExpiryType, Weekday
from app.market.exchanges.models import DEFAULT_UNDERLYINGS
from app.market.expiries.models import ExpiryRecord, ExpiryRule
from app.market.repositories.data_loader import MarketDataLoader

logger = get_logger(__name__)


class ExpiryRepository:
    """In-memory expiry rules and generated expiry records."""

    def __init__(self, seed_directory: Path | None = None) -> None:
        """Initialize repository."""
        self._seed_directory = seed_directory
        self._rules: list[ExpiryRule] = []
        self._records: list[ExpiryRecord] = []

    def initialize(self) -> None:
        """Load expiry rules."""
        self._rules = self._build_default_rules()
        self._records = []
        self._load_seed_files()
        logger.info("Expiry repository loaded {count} rules", count=len(self._rules))

    def close(self) -> None:
        """Clear repository data."""
        self._rules.clear()
        self._records.clear()

    def get_rules(self, underlying: str) -> list[ExpiryRule]:
        """Return expiry rules for an underlying."""
        symbol = underlying.upper()
        return [rule for rule in self._rules if rule.underlying.upper() == symbol]

    def get_expiries(
        self,
        underlying: str,
        *,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[ExpiryRecord]:
        """Return cached expiry records."""
        symbol = underlying.upper()
        records = [item for item in self._records if item.underlying.upper() == symbol]
        if from_date:
            records = [item for item in records if item.expiry_date >= from_date]
        if to_date:
            records = [item for item in records if item.expiry_date <= to_date]
        return records

    def save_rule(self, rule: ExpiryRule) -> None:
        """Save an expiry rule."""
        self._rules.append(rule)

    def save_expiry(self, record: ExpiryRecord) -> None:
        """Save an expiry record."""
        self._records.append(record)

    def _build_default_rules(self) -> list[ExpiryRule]:
        """Build default expiry rules from underlying master."""
        rules: list[ExpiryRule] = []
        for underlying in DEFAULT_UNDERLYINGS:
            if underlying.weekly_expiry_day:
                rules.append(
                    ExpiryRule(
                        underlying=underlying.symbol,
                        expiry_type=ExpiryType.WEEKLY,
                        weekday=Weekday(underlying.weekly_expiry_day),
                    )
                )
            if underlying.monthly_expiry_day:
                rules.append(
                    ExpiryRule(
                        underlying=underlying.symbol,
                        expiry_type=ExpiryType.MONTHLY,
                        weekday=Weekday(underlying.monthly_expiry_day),
                        rule="LAST_WEEKDAY",
                    )
                )
        return rules

    def _load_seed_files(self) -> None:
        """Load expiry rules from seed files."""
        if self._seed_directory is None:
            return
        loader = MarketDataLoader()
        for path in sorted(self._seed_directory.glob("expiry_rules.*")):
            for record in loader.load_records(path):
                self._rules.append(ExpiryRule.model_validate(record))
