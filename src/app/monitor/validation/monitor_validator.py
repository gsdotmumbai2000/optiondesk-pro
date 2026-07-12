"""Monitor input validation."""

from app.market_data.models.snapshot import MarketSnapshot
from app.monitor.exceptions import InvalidMonitorInput
from app.monitor.models.alert import AlertRule
from app.monitor.models.request import MonitorAnalysisRequest
from app.portfolio.models.result import PortfolioResult


class MonitorValidator:
    """Validate monitor inputs and thresholds."""

    def validate_request(self, request: MonitorAnalysisRequest) -> None:
        """Validate analysis request."""
        if not request.session_id:
            raise InvalidMonitorInput("session_id is required")
        self._validate_portfolio(request.portfolio_result)
        self._validate_rules(request.rules)
        if request.market_snapshot is not None:
            self._validate_snapshot(request.market_snapshot)

    def validate_rule(self, rule: AlertRule) -> None:
        """Validate single alert rule."""
        if not rule.rule_id:
            raise InvalidMonitorInput("rule_id is required")
        if not rule.name:
            raise InvalidMonitorInput("rule name is required")

    def _validate_portfolio(self, portfolio: PortfolioResult) -> None:
        if portfolio.cash_balance < 0:
            raise InvalidMonitorInput("cash balance cannot be negative")

    def _validate_rules(self, rules: tuple[AlertRule, ...]) -> None:
        for rule in rules:
            self.validate_rule(rule)

    def _validate_snapshot(self, snapshot: MarketSnapshot) -> None:
        if not snapshot.snapshot_id:
            raise InvalidMonitorInput("market_snapshot must include snapshot_id")
