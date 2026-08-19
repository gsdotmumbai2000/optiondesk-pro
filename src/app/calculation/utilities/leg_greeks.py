"""Solve implied volatility and Greeks for a single option leg.

Used to backfill Delta/Gamma/Theta/Vega for option-chain display when the
broker feed supplies neither (Breeze's option-chain-quotes and tick payloads
carry price/OI/volume only). Reuses the same frozen Black-Scholes pricing
and Greeks engines the rest of the app relies on, fed by a minimal
``CalculationContext`` built from just the inputs a single leg needs
(spot, strike, expiry, rate, dividend, volatility) -- the wider context
fields (option chain snapshot, market session, etc.) aren't read by either
engine for this calculation, so placeholders are used there.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.models.configuration import CalculationConfiguration
from app.calculation.models.enums import MarketSessionType
from app.calculation.models.market_session import MarketSession
from app.calculation.models.snapshots import SpotQuoteSnapshot
from app.calculation.providers.dividend_provider import DividendProvider
from app.calculation.providers.interest_rate_provider import InterestRateProvider
from app.calculation.utilities.time_utils import (
    calculate_days_to_expiry,
    calculate_fractional_year,
    calculate_time_to_expiry_seconds,
)
from app.greeks.engine.greeks_calculator import GreeksCalculator
from app.pricing.black_scholes.engine import BlackScholesEngine
from app.pricing.black_scholes.solver import implied_volatility
from app.pricing.models.enums import OptionType
from app.pricing.models.option_contract import OptionContract
from app.pricing.utilities.decimal_utils import to_decimal

_RATES = InterestRateProvider()
_DIVIDEND = DividendProvider()
_PRICER = BlackScholesEngine()
_CALCULATOR = GreeksCalculator()


@dataclass(frozen=True, slots=True)
class LegGreeks:
    """Solved IV and Greeks for one option leg, or all-None when unusable."""

    implied_volatility: Decimal | None = None
    delta: Decimal | None = None
    gamma: Decimal | None = None
    theta: Decimal | None = None
    vega: Decimal | None = None


_EMPTY = LegGreeks()


def compute_leg_greeks(
    *,
    underlying: str,
    exchange: str,
    ltp: Decimal | None,
    spot: Decimal | None,
    strike: Decimal,
    expiry_date: date,
    option_type: OptionType,
    now: datetime,
    known_iv: Decimal | None = None,
) -> LegGreeks:
    """Solve IV from ``ltp`` (unless ``known_iv`` is already usable) and
    compute Greeks via the frozen Black-Scholes engines.

    Returns an all-None result when inputs are unusable: missing/non-positive
    price or spot, at-or-past expiry, or no IV solution in range (stale or
    crossed quote).
    """
    if ltp is None or ltp <= 0 or spot is None or spot <= 0 or strike <= 0:
        return _EMPTY

    seconds = calculate_time_to_expiry_seconds(now, expiry_date)
    if seconds <= 0:
        return _EMPTY
    time_to_expiry = calculate_fractional_year(seconds)

    rate = _RATES.risk_free_rate()
    dividend = _DIVIDEND.dividend_yield()

    volatility = known_iv if known_iv is not None and known_iv > 0 else None
    if volatility is None:
        solved = implied_volatility(
            float(ltp),
            float(spot),
            float(strike),
            float(rate),
            float(dividend),
            float(time_to_expiry),
            option_type,
        )
        if solved is None:
            return _EMPTY
        volatility = to_decimal(solved, places="0.000001")

    context = CalculationContext(
        underlying=underlying,
        spot_price=spot,
        future_price=None,
        underlying_symbol=underlying,
        exchange=exchange,
        expiry=expiry_date,
        current_time=now,
        trade_date=now.date(),
        market_status="OPEN",
        interest_rate=_RATES.interest_rate(),
        dividend_yield=dividend,
        risk_free_rate=rate,
        volatility=volatility,
        historical_volatility=None,
        implied_volatility=volatility,
        days_to_expiry=calculate_days_to_expiry(now.date(), expiry_date),
        time_to_expiry=time_to_expiry,
        atm_strike=strike,
        lot_size=1,
        tick_size=Decimal("0.05"),
        strike_interval=Decimal("0"),
        currency="INR",
        market_session=MarketSession(
            exchange=exchange,
            session_type=MarketSessionType.REGULAR,
            is_open=True,
            trade_date=str(now.date()),
        ),
        option_chain_snapshot=None,
        future_quote=None,
        spot_quote=SpotQuoteSnapshot(symbol=underlying, exchange=exchange, ltp=spot, timestamp=now),
        configuration=CalculationConfiguration(),
        calculation_timestamp=now,
    )
    contract = OptionContract(strike=strike, option_type=option_type, expiry=expiry_date, multiplier=1)
    pricing = _PRICER.price(context, contract)
    greeks = _CALCULATOR.calculate(context, contract, pricing)
    return LegGreeks(
        implied_volatility=volatility,
        delta=greeks.delta,
        gamma=greeks.gamma,
        theta=greeks.theta,
        vega=greeks.vega,
    )
