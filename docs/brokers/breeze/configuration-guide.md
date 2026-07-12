# Breeze Configuration Guide

## broker.yaml

Non-secret broker settings live in `config/broker.yaml` (overridden by user config in the data directory).

```yaml
schema_version: 1
broker_code: BREEZE
account_name: Default
user_id: ""                    # ICICI Direct user id (display only)
environment: production        # production | sandbox
websocket_enabled: true
auto_login: true               # authenticate on connect when credentials exist
reconnect_max_retries: 5
reconnect_backoff_ms: 2000
session_timeout_min: 480
rate_limit_per_second: 10
```

## Secrets (CredentialManager)

Never place these in YAML. Store via **Broker → Settings** or programmatically:

| Credential | Storage Key |
|------------|-------------|
| API Key | `breeze_api_key:{account_name}` |
| API Secret | `breeze_api_secret:{account_name}` |
| Session Token | `breeze_session_token:{account_name}` |

On Windows, credentials are encrypted with DPAPI via Windows Credential Manager under service name `OptionDeskPro`.

## Environment

| Value | Description |
|-------|-------------|
| `production` | Live ICICI Breeze API |
| `sandbox` | Sandbox / test environment |

Set `environment` in `broker.yaml`. The value is shown in the status bar.

## Session Metadata

After successful login, non-secret metadata is written to:

`{data_directory}/broker/breeze_session.json`

This enables session restore after application restart. The session token itself remains only in `CredentialManager`.

## Dependency Injection

Services are registered in `ApplicationKernel`:

- `ServiceKeys.BROKER` → `BrokerProvider`
- `BrokerWorkspaceService` and `ConnectionStatusService` are wired into `ApplicationProvider` and passed to `DesktopApplication`.

No global singletons are used for broker state.

## Obtaining Breeze Credentials

1. Register at [ICICI Direct API](https://api.icicidirect.com/apiuser/home) and create an app.
2. Note the API key and secret.
3. Use the official login URL to obtain a daily session token.
4. Enter credentials in OptionDesk Pro via **Broker → Settings** and **Broker → Login**.
