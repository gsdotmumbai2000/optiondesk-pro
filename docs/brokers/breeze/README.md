# ICICI Breeze Authentication & Session Management

Production integration of the official ICICI Breeze API into the OptionDesk Pro Broker Framework.

## Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| `BreezeBrokerAdapter` | `src/app/brokers/breeze/broker_adapter.py` | Broker interface implementation |
| `BreezeAuthenticationService` | `src/app/brokers/breeze/authentication_service.py` | Login, logout, reconnect, validation |
| `BreezeSessionManager` | `src/app/brokers/breeze/session_manager.py` | Session lifecycle and timeout |
| `BreezeConfigurationProvider` | `src/app/brokers/breeze/configuration_provider.py` | Config + credential resolution |
| `ConnectionStatusService` | `src/app/services/broker/connection_status_service.py` | User-facing connection status |
| `BrokerWorkspaceService` | `src/app/application/services/broker_workspace_service.py` | Application-layer API for UI |

## Quick Start

1. Configure non-secret settings in `config/broker.yaml` (see [Configuration Guide](configuration-guide.md)).
2. Open **Broker → Settings** and store API key and secret (Windows Credential Manager).
3. Open **Broker → Login**, launch the official Breeze login page, paste the session token.
4. Connection status appears in the status bar.

## Official SDK

Uses the official `breeze-connect` Python SDK. Authentication follows the documented OAuth flow:

`https://api.icicidirect.com/apiuser/login?api_key={encoded_key}`

## Related Documentation

- [Authentication Flow](authentication-flow.md)
- [Sequence Diagram](sequence-diagram.md)
- [Configuration Guide](configuration-guide.md)
