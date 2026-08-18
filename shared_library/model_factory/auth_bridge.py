"""Auth bridge: Databricks WorkspaceClient credentials for AI Gateway calls.

Never writes tokens into ``os.environ``. Uses ``databricks_connectors`` hub /
``AuthProvider`` / request-scoped ``WorkspaceClient``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from shared_library.databricks_connectors import AuthProvider, ConnectorHub, get_hub
from shared_library.databricks_connectors.utils.exceptions import AuthError

from shared_library.model_factory.exceptions import AuthBridgeError

if TYPE_CHECKING:
    from databricks.sdk import WorkspaceClient


@dataclass(frozen=True)
class GatewayCredentials:
    """Bearer token + optional workspace host for OpenAI-compatible clients."""

    api_key: str
    host: Optional[str] = None


def _extract_bearer_token(headers: dict) -> str:
    """Parse ``Authorization: Bearer <token>`` (case-insensitive)."""
    if not isinstance(headers, dict):
        raise AuthBridgeError(
            f"authenticate() returned {type(headers).__name__}, expected dict"
        )

    auth_value: Optional[str] = None
    for key, value in headers.items():
        if str(key).lower() == "authorization":
            auth_value = str(value).strip()
            break

    if not auth_value:
        raise AuthBridgeError("Auth headers missing Authorization value")

    parts = auth_value.split(None, 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1].strip()
    else:
        token = auth_value

    if not token:
        raise AuthBridgeError("Resolved Databricks bearer token is empty")
    return token


def resolve_gateway_credentials(
    hub: Optional[ConnectorHub] = None,
    provider: Optional[AuthProvider] = None,
    workspace_client: Optional["WorkspaceClient"] = None,
) -> GatewayCredentials:
    """Resolve AI Gateway API key from Databricks auth (no env mutation).

    Preference order:
    1. Explicit ``provider``
    2. Explicit ``workspace_client`` (OBO / request-scoped)
    3. Explicit ``hub``
    4. Process default ``get_hub()``
    """

    def _resolve() -> GatewayCredentials:
        try:
            if provider is not None:
                headers = provider.get_auth_headers()
                host = getattr(provider.get_config(), "host", None)
            elif workspace_client is not None:
                cfg = getattr(workspace_client, "config", None)
                if cfg is None or not hasattr(cfg, "authenticate"):
                    raise AuthBridgeError(
                        "WorkspaceClient has no config.authenticate() for AI Gateway"
                    )
                headers = cfg.authenticate()
                host = getattr(cfg, "host", None)
            else:
                resolved_hub = hub if hub is not None else get_hub()
                headers = resolved_hub.get_auth_headers()
                host = getattr(resolved_hub.config, "host", None)
        except AuthError as exc:
            raise AuthBridgeError(f"Databricks auth failed: {exc}") from exc
        except AuthBridgeError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise AuthBridgeError(
                f"Failed to resolve gateway credentials: {exc}"
            ) from exc

        creds = GatewayCredentials(
            api_key=_extract_bearer_token(headers),
            host=str(host).rstrip("/") if host else None,
        )
        return creds

    try:
        import mlflow
        from mlflow.entities import SpanType
        from urllib.parse import urlparse

        with mlflow.start_span(
            name="resolve_gateway_credentials",
            span_type=SpanType.CHAIN,
        ) as span:
            if provider is not None:
                auth_source = "explicit_provider"
            elif workspace_client is not None:
                auth_source = "workspace_client"
            elif hub is not None:
                auth_source = "explicit_hub"
            else:
                auth_source = "default_hub"
            span.set_inputs({"auth_source": auth_source})
            creds = _resolve()
            host_out = None
            if creds.host:
                try:
                    host_out = urlparse(creds.host).netloc or creds.host
                except Exception:  # noqa: BLE001
                    host_out = creds.host
            span.set_outputs(
                {
                    "auth_source": auth_source,
                    "host": host_out,
                    "has_api_key": bool(creds.api_key),
                }
            )
            return creds
    except ImportError:
        return _resolve()
