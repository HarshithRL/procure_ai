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


@dataclass(frozen=True)
class EnvironmentConfig:
    """Immutable environment configuration."""

    # Databricks workspace
    host: str = field(default_factory=lambda: os.getenv("DATABRICKS_HOST", "http://localhost:8001"))
    token: Optional[str] = field(default_factory=lambda: os.getenv("DATABRICKS_TOKEN", None))
    profile: str = field(default_factory=lambda: os.getenv("DATABRICKS_PROFILE", "DEFAULT"))

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
    mlflow_tracking_uri: str = field(
        default_factory=lambda: os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    )
    mlflow_experiment: str = field(default_factory=lambda: os.getenv("MLFLOW_EXPERIMENT", "Procure AI"))

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
            host = data.get("databricks", {}).get("host") or os.getenv("DATABRICKS_HOST", "http://localhost:8001")
            token = data.get("databricks", {}).get("token") or os.getenv("DATABRICKS_TOKEN")
            profile = data.get("databricks", {}).get("profile") or os.getenv("DATABRICKS_PROFILE", "DEFAULT")
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
