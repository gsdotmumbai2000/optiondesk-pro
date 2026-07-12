"""Calculation configuration model."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CalculationConfiguration:
    """Immutable calculation configuration snapshot."""

    risk_free_rate: str = "default"
    dividend_model: str = "none"
    volatility_model: str = "implied"
    calendar_code: str = "NSE"
    metadata: dict[str, str] = field(default_factory=dict)
