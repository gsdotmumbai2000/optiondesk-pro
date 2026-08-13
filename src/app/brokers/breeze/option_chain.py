"""Breeze option chain service."""

from datetime import datetime
from decimal import Decimal

from app.brokers.breeze.client_port import BreezeClientPort
from app.brokers.breeze.normalizers.option_chain_normalizer import \
    normalize_option_chain
from app.brokers.breeze.utilities import unwrap_success
from app.brokers.shared.enums import OptionRight
from app.brokers.shared.models import OptionChain, OptionChainRequest
from app.logging.logging_manager import get_logger

logger = get_logger(__name__)

_BOTH_SIDES: tuple[OptionRight, ...] = (OptionRight.CALL, OptionRight.PUT)


def _to_breeze_iso_expiry(expiry_date: str) -> str:
    """Convert a DD-Mon-YYYY expiry date to the ISO-8601 form Breeze's
    get_option_chain_quotes() requires.

    Breeze's own bundled SDK documentation shows get_quotes() taking
    expiry_date in DD-MMM-YYYY form (e.g. "27-Feb-2025"), but every
    documented get_option_chain_quotes() example — for both the CALL and
    PUT calls — passes expiry_date as ISO-8601
    (e.g. "2025-08-28T06:00:00.000Z"); the two endpoints do not share a
    format. request.expiry_date stays in DD-Mon-YYYY everywhere else
    (cache keys, normalizer, UI) — this conversion is local to the
    outgoing SDK request only.
    """
    parsed = datetime.strptime(expiry_date, "%d-%b-%Y")
    return parsed.strftime("%Y-%m-%dT06:00:00.000Z")


class BreezeOptionChain:
    """Fetch option chain data from Breeze."""

    def __init__(self, client: BreezeClientPort) -> None:
        """Initialize option chain service."""
        self._client = client

    def get_option_chain(
        self,
        request: OptionChainRequest,
        *,
        spot_price: Decimal | None = None,
        atm_strike: Decimal | None = None,
    ) -> OptionChain:
        """Return normalized option chain.

        Breeze's option-chain quotes endpoint requires at least two of
        (expiry_date, right, strike_price). When no explicit side is
        requested, a full chain therefore needs one CALL request and one
        PUT request (never one request per strike); their rows are merged
        by strike in the normalizer.
        """
        rights = (request.right,) if request.right is not None else _BOTH_SIDES
        rows: list[dict] = []
        logger.info(
            "BreezeOptionChain.get_option_chain: underlying={underlying} "
            "exchange={exchange} expiry_date={expiry_date} rights={rights}",
            underlying=request.underlying,
            exchange=request.exchange,
            expiry_date=request.expiry_date,
            rights=[right.value for right in rights],
        )
        for right in rights:
            params = {
                "stock_code": request.underlying,
                "exchange_code": request.exchange.upper(),
                "expiry_date": _to_breeze_iso_expiry(request.expiry_date),
                "product_type": "options",
                "right": right.value.lower(),
                "strike_price": str(request.strike_price or ""),
            }
            logger.info(
                "BEFORE Breeze get_option_chain_quotes(...) params={params}",
                params=params,
            )
            response = self._client.get_option_chain_quotes(**params)
            logger.info(
                "AFTER Breeze get_option_chain_quotes(...) right={right}",
                right=params["right"],
            )
            response_is_dict = isinstance(response, dict)
            logger.debug(
                "Breeze get_option_chain_quotes response boundary: right={right} "
                "response_type={response_type} is_dict={is_dict} keys={keys} "
                "status={status} error_key_present={error_key_present} "
                "error_value={error_value!r} success_type={success_type}",
                right=params["right"],
                response_type=type(response).__name__,
                is_dict=response_is_dict,
                keys=sorted(response.keys()) if response_is_dict else None,
                status=response.get("Status") if response_is_dict else None,
                error_key_present=("Error" in response) if response_is_dict else None,
                error_value=response.get("Error") if response_is_dict else None,
                success_type=type(response.get("Success")).__name__ if response_is_dict else None,
            )
            logger.debug("BEFORE unwrap_success(response) right={right}", right=params["right"])
            payload = unwrap_success(response)
            logger.debug(
                "AFTER unwrap_success(response) right={right} payload_type={payload_type} "
                "payload_len={payload_len}",
                right=params["right"],
                payload_type=type(payload).__name__,
                payload_len=(len(payload) if isinstance(payload, (list, dict, str)) else None),
            )
            if isinstance(payload, list):
                rows.extend(row for row in payload if isinstance(row, dict))
        logger.debug(
            "Merged CALL/PUT rows structure: total_rows={total} sample_row_keys={sample_keys}",
            total=len(rows),
            sample_keys=sorted(rows[0].keys()) if rows else [],
        )
        logger.debug("Option chain normalizer starting: row_count={count}", count=len(rows))
        chain = normalize_option_chain(
            request.underlying,
            request.exchange,
            request.expiry_date,
            rows,
            spot_price=spot_price,
            atm_strike=atm_strike,
        )
        logger.debug(
            "Option chain normalizer completed: strike_count={count}",
            count=len(chain.rows),
        )
        return chain
