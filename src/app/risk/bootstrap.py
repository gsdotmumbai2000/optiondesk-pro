"""Risk engine bootstrap."""

from app.events.event_bus import EventBus
from app.risk.cache.risk_cache import RiskCache
from app.risk.engine.risk_engine import RiskEngine
from app.risk.services.risk_limit_service import RiskLimitService
from app.risk.services.risk_service import RiskService
from app.risk.services.scenario_service import ScenarioService
from app.risk.services.stress_test_service import StressTestService
from app.risk.services.var_service import VaRService
from app.risk.validation.risk_validator import RiskValidator


class RiskProvider:
    """Wire risk engine dependencies."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize provider."""
        self.engine = RiskEngine()
        self.validator = RiskValidator()
        self.cache = RiskCache()
        self.var_service = VaRService(self.engine.var_calculator)
        self.stress_service = StressTestService(self.engine.stress_calculator)
        self.limit_service = RiskLimitService()
        self.scenario_service = ScenarioService()
        self.service = RiskService(
            self.engine,
            self.validator,
            self.cache,
            event_bus,
            self.scenario_service,
        )
