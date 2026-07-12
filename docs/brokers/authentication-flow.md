# Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant CM as CredentialManager
    participant Auth as BreezeAuthentication
    participant SDK as BreezeConnect

    User->>CM: store_api_key/secret/session_token
    Auth->>CM: get credentials
    Auth->>SDK: generate_session(api_secret, session_token)
    SDK-->>Auth: Success
    Auth->>SDK: get_customer_details(api_session)
    SDK-->>Auth: profile
```

Official login URL: `https://api.icicidirect.com/apiuser/login?api_key={encoded_key}`

Session tokens expire daily. Use `refresh_session()` before timeout configured in `broker.yaml`.
