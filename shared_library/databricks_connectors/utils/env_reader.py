"""Environment configuration reader for the Databricks connector.

Reads ``ops/config/{ENV_PROFILE}.yml`` and process env. Never writes OBO
tokens or client secrets back into ``os.environ``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger("databricks_connectors.env_reader")

_VALID_PROFILES = frozenset({"dev", "test", "prod"})
_APP_ENV_ALIASES = {
    "local": "dev",
    "development": "dev",
    "staging": "test",
    "production": "prod",
}

# Package → project root: .../shared_libraries/databricks_connectors/utils/this.py
_PACKAGE_OPS_CONFIG_DIR = Path(__file__).resolve().parents[3] / "ops" / "config"


def resolve_env_profile(explicit: Optional[str] = None) -> str:
    """Resolve ``ENV_PROFILE`` / ``APP_ENV`` to ``dev`` | ``test`` | ``prod``."""
    raw = (explicit or os.environ.get("ENV_PROFILE") or os.environ.get("APP_ENV") or "dev")
    raw = str(raw).strip().lower()
    raw = _APP_ENV_ALIASES.get(raw, raw)
    if raw not in _VALID_PROFILES:
        logger.warning("Unknown env profile %r; falling back to 'dev'", raw)
        return "dev"
    return raw


def resolve_config_dir(explicit: Optional[Path | str] = None) -> Path:
    """Resolve ops config directory without hard-coded machine paths."""
    if explicit:
        return Path(explicit)

    env_dir = os.environ.get("DATABRICKS_CONFIG_DIR")
    if env_dir:
        return Path(env_dir)

    if _PACKAGE_OPS_CONFIG_DIR.is_dir():
        return _PACKAGE_OPS_CONFIG_DIR

    cwd = Path.cwd()
    for candidate in (
        cwd / "ops" / "config",
        cwd / "config",
        cwd.parent / "ops" / "config",
    ):
        if candidate.is_dir():
            return candidate.resolve()

    return _PACKAGE_OPS_CONFIG_DIR


class EnvironmentConfig:
    """Thread-safe-ish config snapshot for one connector construction."""

    def __init__(
        self,
        config_dir: Optional[Path | str] = None,
        env_profile: Optional[str] = None,
    ) -> None:
        self.env_profile = resolve_env_profile(env_profile)
        self.app_env = self.env_profile  # alias used by FastAPI blueprints
        self.config_dir = resolve_config_dir(config_dir)
        self.config_data: Dict[str, Any] = self._load_yaml()
        self._databricks: Dict[str, Any] = {}
        raw_db = self.config_data.get("databricks")
        if isinstance(raw_db, dict):
            self._databricks = raw_db

    def _load_yaml(self) -> Dict[str, Any]:
        path = self.config_dir / f"{self.env_profile}.yml"
        if not path.is_file():
            alt = self.config_dir / f"{self.env_profile}.yaml"
            path = alt if alt.is_file() else path
        if not path.is_file():
            logger.warning(
                "Config file %s not found; using process environment only",
                path,
            )
            return {"env": self.env_profile}

        try:
            with path.open(encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
        except Exception as exc:
            raise ValueError(f"Failed to parse configuration {path}: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(f"Expected mapping in {path}, got {type(data).__name__}")
        data.setdefault("env", self.env_profile)
        logger.info("Loaded EnvironmentConfig profile=%s path=%s", self.env_profile, path)
        return data

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Priority: process env (DATABRICKS_* / upper) > YAML databricks/root > default."""
        friendly_env = {
            "host": "DATABRICKS_HOST",
            "databricks_host": "DATABRICKS_HOST",
            "config_profile": "DATABRICKS_CONFIG_PROFILE",
            "databricks_config_profile": "DATABRICKS_CONFIG_PROFILE",
            "account_id": "DATABRICKS_ACCOUNT_ID",
            "databricks_account_id": "DATABRICKS_ACCOUNT_ID",
            "client_id": "DATABRICKS_CLIENT_ID",
            "databricks_client_id": "DATABRICKS_CLIENT_ID",
            "client_secret": "DATABRICKS_CLIENT_SECRET",
            "databricks_client_secret": "DATABRICKS_CLIENT_SECRET",
            "workspace_id": "DATABRICKS_WORKSPACE_ID",
            "http_timeout_seconds": "DATABRICKS_HTTP_TIMEOUT_SECONDS",
            "connection_pool_size": "DATABRICKS_CONNECTION_POOL_SIZE",
            "auth_mode": "DATABRICKS_AUTH_MODE",
        }
        mapped = friendly_env.get(key.lower())
        if mapped and mapped in os.environ and os.environ[mapped] != "":
            return os.environ[mapped]

        env_key = key.upper()
        if env_key in os.environ and os.environ[env_key] != "":
            return os.environ[env_key]
        prefixed = f"DATABRICKS_{env_key}" if not env_key.startswith("DATABRICKS_") else env_key
        if prefixed in os.environ and os.environ[prefixed] != "":
            return os.environ[prefixed]

        if key in self._databricks and self._databricks[key] not in (None, ""):
            return self._databricks[key]
        if key in self.config_data and self.config_data[key] not in (None, ""):
            return self.config_data[key]

        yaml_aliases = {
            "databricks_host": "host",
            "databricks_config_profile": "config_profile",
            "databricks_account_id": "account_id",
            "databricks_client_id": "client_id",
            "databricks_client_secret": "client_secret",
        }
        alias = yaml_aliases.get(key)
        if alias and alias in self._databricks and self._databricks[alias] not in (None, ""):
            return self._databricks[alias]

        return default

    @property
    def is_local(self) -> bool:
        """Local/dev/test tiers (CLI profile / U2M)."""
        return self.env_profile in ("dev", "test")

    @property
    def is_production(self) -> bool:
        return self.env_profile == "prod"

    @property
    def auth_mode(self) -> str:
        return str(self.get("auth_mode", "profile" if self.is_local else "apps_sp"))

    @property
    def host(self) -> Optional[str]:
        value = self.get("host") or self.get("databricks_host")
        return str(value).rstrip("/") if value else None

    @property
    def config_profile(self) -> Optional[str]:
        value = self.get("config_profile") or self.get("databricks_config_profile")
        return str(value) if value else None

    @property
    def account_id(self) -> Optional[str]:
        value = self.get("account_id") or self.get("databricks_account_id")
        return str(value) if value else None

    @property
    def workspace_id(self) -> Optional[str]:
        value = self.get("workspace_id")
        return str(value) if value else None

    @property
    def http_timeout_seconds(self) -> int:
        raw = self.get("http_timeout_seconds", 30)
        try:
            return int(raw)
        except (TypeError, ValueError):
            return 30

    @property
    def connection_pool_size(self) -> int:
        """Process hub pool size (OBO clients use a smaller isolated pool of 10)."""
        raw = self.get("connection_pool_size", 100)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return 100
        return max(1, value)

    def sdk_config_kwargs(
        self,
        *,
        host: Optional[str] = None,
        profile: Optional[str] = None,
        token: Optional[str] = None,
        account_id: Optional[str] = None,
        connection_pool_size: Optional[int] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        """Build isolated SDK ``Config`` kwargs (no os.environ mutation)."""
        pool = (
            connection_pool_size
            if connection_pool_size is not None
            else self.connection_pool_size
        )
        kwargs: Dict[str, Any] = {
            "http_timeout_seconds": self.http_timeout_seconds,
            "connection_pool_size": pool,
            **extra,
        }
        resolved_host = host or self.host
        if resolved_host:
            kwargs["host"] = resolved_host

        if token is not None:
            kwargs["token"] = token
        else:
            resolved_profile = profile or self.config_profile
            if resolved_profile:
                kwargs["profile"] = resolved_profile
            client_id = os.environ.get("DATABRICKS_CLIENT_ID")
            client_secret = os.environ.get("DATABRICKS_CLIENT_SECRET")
            if client_id and client_secret and not self.is_local:
                kwargs["client_id"] = client_id
                kwargs["client_secret"] = client_secret

        resolved_account = account_id or self.account_id
        if resolved_account:
            kwargs["account_id"] = resolved_account

        return kwargs

