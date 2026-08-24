"""Today (time-decayed) payoff analytics.

Unlike expiry_payoff.py (pure intrinsic value), this reprices each leg with
the Black-Scholes engine at a hypothetical spot while holding time-to-expiry
and rates fixed at the strategy's current context -- giving a real "if the
underlying were at X right now" valuation instead of the expiry-only view.

Each leg is repriced at its *own* current market implied volatility --
the live chain's quoted IV for that strike/side, or one solved from the
chain's live traded price when no IV is quoted -- rather than one shared
context.volatility applied to every strike. Strikes typically carry
different real market IV (skew), and platforms like Groww/Sensibull/Opstra
all price legs off their own IV rather than a single blended number for the
whole strategy.

Deliberately NOT solved from the leg's own *stored entry premium*: doing so
anchored at the context's current spot is circular for the single most
important use of this module (today's live P&L at the actual current spot)
-- it solves "what vol would make this leg's live price equal to what I
paid", then evaluates the leg at that same current spot, which is zero by
construction regardless of how the underlying has actually moved since
entry. The live chain's own quote has no such dependency on the leg's
history. Falls back to context.volatility only when the chain has no
strike/side match or usable quote at all (e.g. in tests, or legs whose
strike isn't in the currently loaded chain window) -- the same behaviour as
before per-leg IV existed.

Known limitation, not fixed here: BlackScholesEngine.price() reads only
context.time_to_expiry, never contract.expiry, so legs with a different
expiry than the context (calendar/diagonal spreads) are all priced off one
shared time-to-expiry.
"""

import dataclasses
from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.payoff.analytics.payoff_curve import DEFAULT_SAMPLES, price_bounds, sample_prices
from app.payoff.models.legs import StrategyLeg
from app.payoff.models.result import PayoffCurve, PayoffCurvePoint
from app.pricing.black_scholes.engine import BlackScholesEngine
from app.pricing.black_scholes.solver import implied_volatility as solve_bs_iv
from app.pricing.models.enums import OptionType
from app.pricing.models.option_contract import OptionContract

_ENGINE = BlackScholesEngine()


def _leg_market_volatility(leg: StrategyLeg, context: CalculationContext) -> Decimal:
    """Resolve this leg's own current market IV from the live option chain
    in context: its quoted IV when published, else solved from its live
    traded price at the chain's own (current) spot. Falls back to
    context.volatility when the chain has no match/usable quote for this
    strike/side."""
    snapshot = context.option_chain_snapshot
    if snapshot is not None:
        for strike in snapshot.strikes:
            if strike.strike_price != leg.strike:
                continue
            iv, ltp = (
                (strike.call_iv, strike.call_ltp)
                if leg.option_type == OptionType.CALL
                else (strike.put_iv, strike.put_ltp)
            )
            if iv is not None and iv > 0:
                return iv
            if ltp is not None and ltp > 0:
                solved = solve_bs_iv(
                    float(ltp),
                    float(context.spot_price),
                    float(leg.strike),
                    float(context.risk_free_rate),
                    float(context.dividend_yield),
                    float(context.time_to_expiry),
                    leg.option_type,
                )
                if solved is not None:
                    return Decimal(str(solved))
            break
    return context.volatility


def leg_today_pnl(
    price: Decimal,
    leg: StrategyLeg,
    context: CalculationContext,
    *,
    volatility: Decimal | None = None,
) -> Decimal:
    """Return today's (time-decayed) PnL for a single leg at a hypothetical
    spot, repriced at the leg's own current market volatility. Pass
    `volatility` to reuse an already-resolved value (see build_today_curve)
    instead of re-resolving it for every sample price."""
    leg_volatility = volatility if volatility is not None else _leg_market_volatility(leg, context)
    variant_ctx = dataclasses.replace(context, spot_price=price, volatility=leg_volatility)
    contract = OptionContract(strike=leg.strike, option_type=leg.option_type, expiry=leg.expiry, multiplier=1)
    theoretical_price = _ENGINE.price(variant_ctx, contract).theoretical_price
    scale = Decimal(leg.quantity) * Decimal(leg.multiplier)
    return scale * theoretical_price - scale * leg.premium


def total_today_pnl(
    price: Decimal, legs: tuple[StrategyLeg, ...], context: CalculationContext
) -> Decimal:
    """Return aggregate today's PnL across all legs at a hypothetical spot,
    each leg repriced at its own current market volatility (see
    leg_today_pnl)."""
    return sum((leg_today_pnl(price, leg, context) for leg in legs), Decimal("0"))


def build_today_curve(
    legs: tuple[StrategyLeg, ...],
    context: CalculationContext,
    *,
    samples: int = DEFAULT_SAMPLES,
) -> PayoffCurve:
    """Build today's time-decayed payoff curve across the same price range as
    expiry. Each leg's market volatility is resolved once (it depends only
    on the live chain and the context's actual current spot, not the scan
    price) and reused across every sample point."""
    if not legs or samples < 2:
        return PayoffCurve()
    low, high = price_bounds(context, legs)
    if high <= low:
        high = low + context.tick_size
    leg_volatilities = tuple(_leg_market_volatility(leg, context) for leg in legs)
    points = tuple(
        PayoffCurvePoint(
            underlying_price=price,
            pnl=sum(
                (
                    leg_today_pnl(price, leg, context, volatility=vol)
                    for leg, vol in zip(legs, leg_volatilities)
                ),
                Decimal("0"),
            ),
        )
        for price in sample_prices(low, high, samples, legs)
    )
    return PayoffCurve(points=points)
