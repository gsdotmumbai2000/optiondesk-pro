"""Option chain consistency validation."""

from app.live.exceptions import LiveValidationException
from app.live.models.option_chain import LiveOptionChain


class ChainValidator:
    """Validate live option chain consistency."""

    def validate(self, chain: LiveOptionChain) -> None:
        if not chain.underlying.strip():
            raise LiveValidationException("Chain underlying is required")
        if not chain.expiry_date.strip():
            raise LiveValidationException("Chain expiry is required")
        if chain.spot_price is not None and chain.spot_price <= 0:
            raise LiveValidationException("Spot price must be positive")
