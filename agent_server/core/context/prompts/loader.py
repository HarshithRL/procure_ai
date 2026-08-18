"""Prompt loader — disk and MLflow registry."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

_PROMPT_CACHE: dict[str, str] = {}


def load_prompt(agent_name: str, prompt_name: str) -> str:
    """Load a prompt from disk.

    Convention: agent_server/core/context/prompts/{agent_name}/{prompt_name}.md

    Args:
        agent_name: e.g., "brain"
        prompt_name: e.g., "SYSTEM_PROMPT"

    Returns:
        Prompt text (markdown).

    Raises:
        FileNotFoundError: if the prompt file doesn't exist.
    """
    cache_key = f"{agent_name}/{prompt_name}"
    if cache_key in _PROMPT_CACHE:
        return _PROMPT_CACHE[cache_key]

    prompt_dir = Path(__file__).resolve().parent / agent_name
    prompt_file = prompt_dir / f"{prompt_name}.md"

    if not prompt_file.is_file():
        raise FileNotFoundError(f"Prompt not found: {prompt_file}")

    with open(prompt_file, "r", encoding="utf-8") as f:
        content = f.read()

    _PROMPT_CACHE[cache_key] = content
    return content


def get_brain_system_prompt(prefer_registry: bool = True) -> str:
    """Get the Brain agent system prompt from disk or MLflow registry.

    If ``prefer_registry=True``, tries to load from MLflow Prompt Registry first.
    Falls back to disk.

    Args:
        prefer_registry: Try MLflow Prompt Registry first (requires mlflow import).

    Returns:
        System prompt text.
    """
    if prefer_registry:
        try:
            import mlflow
            prompt_uri = f"prompts:/procure-brain-system@production"
            prompt = mlflow.genai.load_prompt(prompt_uri)
            return prompt
        except ImportError:
            pass
        except Exception:
            # Registry unavailable; fall back to disk
            pass

    return load_prompt("brain", "SYSTEM_PROMPT")


def _sync_brain_prompt_to_registry() -> None:
    """Sync Brain system prompt to MLflow Prompt Registry on startup.

    Only registers if content changed (detected via SHA-256 hash).
    """
    try:
        import mlflow
    except ImportError:
        return

    prompt_name = "procure-brain-system"
    content = load_prompt("brain", "SYSTEM_PROMPT")
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    try:
        # Try to fetch the latest version
        latest = mlflow.genai.load_prompt(f"prompts:/{prompt_name}")
        latest_hash = hashlib.sha256(latest.encode()).hexdigest()[:16]

        if content_hash == latest_hash:
            # No change
            return
    except Exception:
        # Version doesn't exist yet; register it
        pass

    # Register new version (or new prompt)
    try:
        mlflow.genai.log_prompt(
            prompt_name,
            prompt_template=content,
            description="Procure AI Brain Agent system prompt",
        )
        # Set alias
        alias = "production"
        mlflow.genai.set_prompt_alias(prompt_name, alias, version=1)
    except Exception:
        # Silent fail on registry issues
        pass
