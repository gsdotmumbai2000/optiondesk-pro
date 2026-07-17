"""Breeze client factory with lazy SDK import."""

from collections.abc import Callable
from typing import cast

from app.brokers.breeze.client_port import BreezeClientPort


def create_breeze_client(api_key: str) -> BreezeClientPort:
    """Create a BreezeConnect client without importing at module load."""
    from breeze_connect import BreezeConnect

    from app.brokers.breeze.sdk_diagnostics import apply_breeze_sdk_diagnostics

    apply_breeze_sdk_diagnostics()
    return cast(BreezeClientPort, BreezeConnect(api_key=api_key))


def resolve_client_factory(
    factory: Callable[[str], object] | None,
) -> Callable[[str], BreezeClientPort]:
    """Resolve injectable client factory."""
    if factory is not None:
        return factory  # type: ignore[return-value]
    return create_breeze_client
