"""UI command identifiers for MVVM layer."""

from enum import Enum


class UICommandId(str, Enum):
    """Standard UI command identifiers."""

    OPEN = "open"
    SAVE = "save"
    REFRESH = "refresh"
    EVALUATE = "evaluate"
    OPTIMIZE = "optimize"
    RUN_BACKTEST = "run_backtest"
    EXPORT = "export"
    GENERATE_RECOMMENDATION = "generate_recommendation"
