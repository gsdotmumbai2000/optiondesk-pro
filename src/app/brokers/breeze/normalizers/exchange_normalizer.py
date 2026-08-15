"""Normalize Breeze's raw websocket exchange labels to canonical exchange codes.

Breeze's streaming tick payloads carry human-readable exchange labels
(``"NSE Equity"``, ``"NSE Futures & Options"``, ...) rather than the
application's canonical exchange codes (``"NSE"``, ``"NFO"``, ...). Confirmed
against the installed breeze_connect SDK's ``parse_data`` (which assigns these
exact strings) and against live NIFTY/BANKNIFTY/FINNIFTY/MIDCPNIFTY cash and
NFO option ticks.
"""

_BREEZE_EXCHANGE_LABEL_MAP: dict[str, str] = {
    "NSE Equity": "NSE",
    "NSE Futures & Options": "NFO",
    "BSE": "BSE",
}


def canonical_exchange(raw_exchange: str) -> str:
    """Map a raw Breeze tick exchange label to a canonical exchange code.

    Unrecognized labels are returned unchanged so an unmapped segment (e.g.
    Breeze's ``"NSE Currency"``/``"Commodity"`` labels, never observed on the
    subscriptions this application makes) is visible downstream rather than
    silently coerced.
    """
    return _BREEZE_EXCHANGE_LABEL_MAP.get(raw_exchange.strip(), raw_exchange)
