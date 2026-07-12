# Breeze Authentication Flow

## Overview

OptionDesk Pro uses the official ICICI Breeze OAuth flow. Secrets are never stored in YAML or logs.

## Steps

1. **Configure** — Set `broker_code`, `account_name`, `user_id`, and `environment` in `broker.yaml`.
2. **Store credentials** — API key, API secret, and session token are stored via `CredentialManager` (Windows DPAPI on Windows).
3. **User login** — User opens the official Breeze login URL (built from API key).
4. **Session token** — User copies the session token from the Breeze redirect and enters it in the Broker Login dialog.
5. **Generate session** — `BreezeAuthenticationService` calls `generate_session(api_secret, session_token)` via the official SDK.
6. **Validate** — `get_customer_details(api_session)` confirms the session is active.
7. **Persist metadata** — Non-secret session metadata is saved to `{data_directory}/broker/breeze_session.json` for restart restore.

## Lifecycle Operations

| Operation | Entry Point | Behavior |
|-----------|-------------|----------|
| Login | `BrokerWorkspaceService.login()` | Connect + authenticate with retry |
| Reconnect | `BrokerWorkspaceService.reconnect()` | Disconnect, reconnect, re-authenticate |
| Restore | `BrokerWorkspaceService.restore_session()` | Load metadata + validate stored token on startup |
| Logout | `BrokerWorkspaceService.logout()` | Clear session, disconnect, remove metadata |
| Health check | `BreezeAuthenticationService.health_check()` | Validate session via API |

## Connection States

| State | Meaning |
|-------|---------|
| Disconnected | No active broker connection |
| Connecting | Connection or authentication in progress |
| Connected | Session valid and broker ready |
| Authentication Failed | Invalid API key, secret, or session token |
| Expired | Session timed out or invalidated by Breeze |
| Reconnect Required | Heartbeat detected session loss |

## Events

| Event | When Published |
|-------|----------------|
| `BrokerConnectedEvent` | Broker connection established |
| `BrokerDisconnectedEvent` | Broker disconnected |
| `AuthenticationSucceededEvent` | Login or reconnect succeeded |
| `AuthenticationFailedEvent` | Login or credential validation failed |
| `SessionExpiredEvent` | Session expired during heartbeat |

## Error Handling

- Invalid API key / session → `BrokerAuthenticationException`, status **Authentication Failed**
- Network / timeout → exponential backoff retry via `retry_call`
- Server errors → logged without secrets, surfaced to UI via events
