"""Application layer enumerations."""

from enum import Enum


class ApplicationModelVersion(str, Enum):
    """Application services schema version."""

    V1 = "application-services-v1"


class WorkspaceType(str, Enum):
    """Application workspace types."""

    TRADING = "TRADING"
    STRATEGY = "STRATEGY"
    PORTFOLIO = "PORTFOLIO"
    BACKTESTING = "BACKTESTING"
    MARKET = "MARKET"
    AI = "AI"
    ORDER = "ORDER"
    SETTINGS = "SETTINGS"


class CommandType(str, Enum):
    """Application command types."""

    OPEN_STRATEGY = "OPEN_STRATEGY"
    SAVE_STRATEGY = "SAVE_STRATEGY"
    RUN_OPTIMIZATION = "RUN_OPTIMIZATION"
    RUN_BACKTEST = "RUN_BACKTEST"
    REFRESH_MARKET = "REFRESH_MARKET"
    GENERATE_REPORT = "GENERATE_REPORT"
    CREATE_STRATEGY = "CREATE_STRATEGY"
    EVALUATE_STRATEGY = "EVALUATE_STRATEGY"
    LOAD_PORTFOLIO = "LOAD_PORTFOLIO"
    REFRESH_PORTFOLIO = "REFRESH_PORTFOLIO"
    GENERATE_RECOMMENDATION = "GENERATE_RECOMMENDATION"


class QueryType(str, Enum):
    """Application query types."""

    GET_PORTFOLIO = "GET_PORTFOLIO"
    GET_MARKET = "GET_MARKET"
    GET_STRATEGY = "GET_STRATEGY"
    GET_REPORTS = "GET_REPORTS"
    GET_RECOMMENDATIONS = "GET_RECOMMENDATIONS"
    GET_WORKSPACE_STATE = "GET_WORKSPACE_STATE"
    GET_SESSION = "GET_SESSION"


class BacktestRunState(str, Enum):
    """Backtest session run state."""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"
