"""Calculation engine orchestrator."""

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.models.configuration import CalculationConfiguration
from app.calculation.services.context_service import CalculationContextService


class CalculationEngine:
    """Enterprise calculation engine entry point."""

    def __init__(self, context_service: CalculationContextService) -> None:
        """Initialize calculation engine."""
        self._context_service = context_service

    @property
    def contexts(self) -> CalculationContextService:
        """Return context service."""
        return self._context_service

    def create_context(
        self,
        underlying: str,
        exchange: str,
        expiry: str,
        *,
        configuration: CalculationConfiguration | None = None,
    ) -> CalculationContext:
        """Create an immutable calculation context."""
        return self._context_service.create_context(
            underlying,
            exchange,
            expiry,
            configuration=configuration,
        )

    def get_latest_context(
        self,
        underlying: str,
        exchange: str,
        expiry: str,
    ) -> CalculationContext | None:
        """Return latest cached context."""
        return self._context_service.get_latest(underlying, exchange, expiry)

    def get_previous_context(
        self,
        underlying: str,
        exchange: str,
        expiry: str,
    ) -> CalculationContext | None:
        """Return previous cached context."""
        return self._context_service.get_previous(underlying, exchange, expiry)

    def compare_contexts(
        self,
        underlying: str,
        exchange: str,
        expiry: str,
    ) -> dict[str, object] | None:
        """Compare latest and previous contexts."""
        return self._context_service.compare_contexts(underlying, exchange, expiry)
