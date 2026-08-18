# databricks_connectors

Enterprise hybrid Databricks connector for the PDF Parser agent/app stack.

**Auth + identity + typo-safe REST** on top of the official Databricks SDK Unified Client Authentication, with optional **FastAPI OBO dependencies**.

## Layout

```text
databricks_connectors/
├── __init__.py
├── hub.py
├── core/
│   ├── auth.py          # AuthProvider / AuthManager factories + httpx
│   └── identity.py      # IdentityManager, WorkspaceUserMetadata, Concierge
├── utils/
│   ├── env_reader.py
│   ├── exceptions.py
│   └── retry.py
└── integrations/
    └── fastapi_deps.py   # Depends: verified_user, Concierge SP handoff
```

## Quick start

```python
from shared_libraries.databricks_connectors import get_hub, ConnectorHub

hub = get_hub()
identity = hub.get_current_identity()
print(identity.user_name, identity.entitlements)

# SDK services (typed)
clusters = list(hub.clusters.list())

# Preview / unmapped REST (explicit only)
payload = hub.rest("GET", "/api/2.0/preview/scim/v2/Users", query={"count": 10})

# Apps OBO
obo = ConnectorHub.from_obo_token(request.headers["x-forwarded-access-token"])
```

## FastAPI wiring

```python
from fastapi import Depends
from shared_libraries.databricks_connectors.integrations.fastapi_deps import (
    AuthenticatedUser,
    verified_user,
    get_sp_client,
)

@router.get("/api/v1/identity/me")
async def me(user: AuthenticatedUser = Depends(verified_user)):
    return user.to_dict()

@router.post("/long-job")
async def long_job(user: AuthenticatedUser = Depends(verified_user)):
    # Concierge: OBO validated → execute as SP / profile hub
    if not user.has_entitlement("allow-jobs-trigger"):
        ...
    sp = get_sp_client()
    ...
```

Agent server exposes:

- `GET /api/v1/identity/me` — control-plane verified caller
- `GET /api/v1/identity/sp` — Concierge probe (SP host)
- `GET /api/v1/identity/entitlement/{name}` — entitlement gate demo

Local/dev uses CLI profile when `X-Forwarded-Access-Token` is absent. Chat `/agents/*` routes are **not** OBO-gated (Streamlit stays working).

## Auth modes

| Mode | When | Credentials |
|------|------|-------------|
| **U2M profile** | `ENV_PROFILE=dev` / `test` | CLI profile + `ops/config/{env}.yml` |
| **M2M Apps SP** | `ENV_PROFILE=prod` | Injected `DATABRICKS_CLIENT_ID` / `SECRET` / `HOST` |
| **OBO** | Per-request | `X-Forwarded-Access-Token` → isolated client |

`Config.http_timeout_seconds` (default **30**) bounds OIDC token refresh.

## Environment config

`EnvironmentConfig` resolves config dir:

1. Constructor `config_dir`
2. `DATABRICKS_CONFIG_DIR`
3. Package-relative `ops/config`
4. CWD `ops/config` / `config`

Priority for values: process env → YAML → defaults. Never writes OBO tokens/secrets into `os.environ`.

`ENV_PROFILE` primary (`dev`|`test`|`prod`); `APP_ENV=local` → `dev`. `is_local` is true for `dev` and `test`.

## Concierge pattern

OBO tokens last ~1 hour. Validate, then hand long work to the SP hub:

```python
from shared_libraries.databricks_connectors import IdentityManager
from shared_libraries.databricks_connectors.integrations.fastapi_deps import get_sp_client

mgr = IdentityManager()
with mgr.user_session(token) as (client, identity):
    mgr.authorize_long_running_task(client, required_entitlement="allow-jobs-trigger")
sp = get_sp_client()  # marathon runner
```

## Design rules

- `__getattr__` only delegates to SDK clients — never invents REST paths
- Use `.rest(method, path, ...)` for preview/unmapped endpoints
- Never set `os.environ["DATABRICKS_TOKEN"]` for per-request identity
- Do not retry HTTP 401/403
