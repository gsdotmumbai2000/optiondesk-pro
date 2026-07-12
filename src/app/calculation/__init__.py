"""Calculation engine package."""

__all__ = ["CalculationContext", "CalculationEngine", "CalculationProvider"]


def __getattr__(name: str) -> object:
    """Lazy exports to avoid import cycles."""
    if name == "CalculationContext":
        from app.calculation.context.calculation_context import CalculationContext

        return CalculationContext
    if name == "CalculationEngine":
        from app.calculation.engine.calculation_engine import CalculationEngine

        return CalculationEngine
    if name == "CalculationProvider":
        from app.calculation.bootstrap import CalculationProvider

        return CalculationProvider
    raise AttributeError(name)
