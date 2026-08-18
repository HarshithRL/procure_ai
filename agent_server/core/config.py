"""Environment configuration loader for Procure AI agent.

Reads from config.yaml (colocated in agent_server/) or environment variables.
Follows the PDF Parser pattern: EnvironmentConfig with workspace host + LLM profile.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


def _ops_config():
    """Load the shared ops/config/{ENV_PROFILE}.yml view, or None if unavailable."""
    try:
        from shared_library.databricks_connectors.utils.env_reader import (
            EnvironmentConfig as OpsEnvironmentConfig,
        )

        return OpsEnvironmentConfig()
    except Exception:
        return None


def resolve_workspace_host() -> str:
    """Resolve the Databricks workspace host.

    Priority: DATABRICKS_HOST env (injected by Databricks Apps) →
    ops/config/{ENV_PROFILE}.yml `databricks.host` → empty string.

    Returns "" rather than a localhost placeholder when nothing is configured:
    a bogus host silently misdirects auth and disables MLflow tracing, whereas
    an empty value makes the missing configuration obvious.
    """
    env_host = os.getenv("DATABRICKS_HOST")
    if env_host:
        return env_host

    ops = _ops_config()
    return (ops.host if ops and ops.host else "") or ""


def resolve_config_profile() -> str:
    """Resolve the ~/.databrickscfg profile name for local U2M auth.

    Priority: DATABRICKS_CONFIG_PROFILE (what the SDK and databricks_connectors
    actually honour) → legacy DATABRICKS_PROFILE → ops/config yml
    `databricks.config_profile` → "DEFAULT".
    """
    for var in ("DATABRICKS_CONFIG_PROFILE", "DATABRICKS_PROFILE"):
        value = os.getenv(var)
        if value:
            return value

    ops = _ops_config()
    if ops and ops.config_profile:
        return ops.config_profile
    return "DEFAULT"


@dataclass(frozen=True)
class EnvironmentConfig:
    """Immutable environment configuration."""

    # Databricks workspace
    host: str = field(default_factory=resolve_workspace_host)
    token: Optional[str] = field(default_factory=lambda: os.getenv("DATABRICKS_TOKEN", None))
    profile: str = field(default_factory=resolve_config_profile)

    # LLM & model routing
    llm_profile: str = field(default_factory=lambda: os.getenv("LLM_PROFILE", "balanced"))
    llm_model: Optional[str] = field(default_factory=lambda: os.getenv("LLM_MODEL", None))

    # Agent persistence
    db_path: str = field(
        default_factory=lambda: os.getenv(
            "AGENT_DB_PATH",
            str(Path(__file__).resolve().parent.parent / "checkpoints.db"),
        )
    )

    # Observability
    # Tracking URI: whenever a real workspace host is resolvable (env var in
    # production, ops/config yml locally) default to the managed tracking
    # server. Otherwise default to empty so tracing is skipped rather than
    # falling back to the deprecated local ./mlruns file store.
    mlflow_tracking_uri: str = field(
        default_factory=lambda: os.getenv("MLFLOW_TRACKING_URI")
        or ("databricks" if resolve_workspace_host() else "")
    )
    # Databricks requires experiment names to be absolute workspace paths.
    mlflow_experiment: str = field(
        default_factory=lambda: os.getenv("MLFLOW_EXPERIMENT", "/Shared/procure_ai")
    )

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_dir: str = field(default_factory=lambda: os.getenv("LOG_DIR", "data/logs"))

    def to_dict(self) -> dict:
        """Serialize to dict for passing to downstream config."""
        return {
            "host": self.host,
            "token": self.token,
            "profile": self.profile,
            "llm_profile": self.llm_profile,
            "llm_model": self.llm_model,
            "db_path": self.db_path,
            "mlflow_tracking_uri": self.mlflow_tracking_uri,
            "mlflow_experiment": self.mlflow_experiment,
            "log_level": self.log_level,
            "log_dir": self.log_dir,
        }


def load_config(config_path: Optional[Path | str] = None) -> EnvironmentConfig:
    """Load configuration from config.yaml if it exists, else use EnvironmentConfig defaults.

    Args:
        config_path: Optional explicit path to config.yaml. Defaults to agent_server/config.yaml.

    Returns:
        EnvironmentConfig instance with all values resolved.
    """
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent / "config.yaml"
    else:
        config_path = Path(config_path)

    # If YAML exists, load it; otherwise use env vars
    if config_path.is_file():
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            # Merge with EnvironmentConfig, preferring YAML values
            host = data.get("databricks", {}).get("host") or resolve_workspace_host()
            token = data.get("databricks", {}).get("token") or os.getenv("DATABRICKS_TOKEN")
            profile = (
                data.get("databricks", {}).get("config_profile")
                or data.get("databricks", {}).get("profile")
                or resolve_config_profile()
            )
            llm_profile = data.get("llm", {}).get("profile") or os.getenv("LLM_PROFILE", "balanced")
            llm_model = data.get("llm", {}).get("model") or os.getenv("LLM_MODEL")

            return EnvironmentConfig(
                host=host,
                token=token,
                profile=profile,
                llm_profile=llm_profile,
                llm_model=llm_model,
            )
    else:
        # Use pure env var resolution
        return EnvironmentConfig()


# Singleton instance (lazy-loaded at first use)
_CONFIG: Optional[EnvironmentConfig] = None


def get_config() -> EnvironmentConfig:
    """Get or create singleton EnvironmentConfig."""
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = load_config()
    return _CONFIG


def reset_config() -> None:
    """Reset singleton (for testing)."""
    global _CONFIG
    _CONFIG = None
