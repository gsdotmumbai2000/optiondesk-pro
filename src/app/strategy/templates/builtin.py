"""Built-in strategy templates."""

from datetime import date
from decimal import Decimal

from app.strategy.models.enums import LegKind, StrategyType
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.template import StrategyTemplate


def _leg(
    leg_id: str,
    kind: LegKind,
    strike: str = "0",
    qty: int = 1,
) -> StrategyLeg:
    return StrategyLeg(
        leg_id=leg_id,
        kind=kind,
        quantity=qty,
        premium=Decimal("0"),
        strike=Decimal(strike),
        expiry=date(2099, 12, 31),
    )


BUILTIN_TEMPLATES: tuple[StrategyTemplate, ...] = (
    StrategyTemplate(
        template_id="long_call",
        name="Long Call",
        strategy_type=StrategyType.LONG_CALL,
        legs=(_leg("1", LegKind.CALL_BUY),),
    ),
    StrategyTemplate(
        template_id="long_put",
        name="Long Put",
        strategy_type=StrategyType.LONG_PUT,
        legs=(_leg("1", LegKind.PUT_BUY),),
    ),
    StrategyTemplate(
        template_id="iron_condor",
        name="Iron Condor",
        strategy_type=StrategyType.IRON_CONDOR,
        legs=(
            _leg("1", LegKind.PUT_BUY, "90"),
            _leg("2", LegKind.PUT_SELL, "95"),
            _leg("3", LegKind.CALL_SELL, "105"),
            _leg("4", LegKind.CALL_BUY, "110"),
        ),
    ),
    StrategyTemplate(
        template_id="long_straddle",
        name="Long Straddle",
        strategy_type=StrategyType.LONG_STRADDLE,
        legs=(
            _leg("1", LegKind.CALL_BUY, "100"),
            _leg("2", LegKind.PUT_BUY, "100"),
        ),
    ),
    StrategyTemplate(
        template_id="bull_call_spread",
        name="Bull Call Spread",
        strategy_type=StrategyType.BULL_CALL_SPREAD,
        legs=(
            _leg("1", LegKind.CALL_BUY, "100"),
            _leg("2", LegKind.CALL_SELL, "110"),
        ),
    ),
)


def get_builtin_templates() -> tuple[StrategyTemplate, ...]:
    """Return all built-in templates."""
    return BUILTIN_TEMPLATES
