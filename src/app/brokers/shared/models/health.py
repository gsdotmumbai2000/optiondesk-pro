"""Broker health domain models."""

from pydantic import BaseModel

from app.brokers.shared.enums import ConnectionState


class BrokerHealth(BaseModel):
    """Broker health snapshot."""

    broker_code: str
    connection_state: ConnectionState
    is_session_valid: bool
    websocket_connected: bool = False
    last_heartbeat: str = ""
    message: str = ""
