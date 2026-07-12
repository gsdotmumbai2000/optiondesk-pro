"""Payoff analytics package."""

from app.payoff.analytics.breakevens import find_breakevens
from app.payoff.analytics.expiry_payoff import leg_expiry_pnl, total_expiry_pnl
from app.payoff.analytics.payoff_curve import build_payoff_curve
from app.payoff.analytics.risk_reward import risk_reward_ratio
from app.payoff.analytics.risk_table import build_risk_table, curve_extrema

__all__ = [
    "build_payoff_curve",
    "build_risk_table",
    "curve_extrema",
    "find_breakevens",
    "leg_expiry_pnl",
    "risk_reward_ratio",
    "total_expiry_pnl",
]
