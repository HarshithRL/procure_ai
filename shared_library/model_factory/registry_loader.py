"""Load and validate colocated Model Factory YAML registries."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from shared_library.model_factory.exceptions import RegistryError

_DEFAULT_REGISTRIES_DIR = Path(__file__).resolve().parent / "registries"

_REQUIRED_FILES = (
    "ProviderRegistry.yaml",
    "ModelRegistry.yaml",
    "ProfileRegistry.yaml",
    "CapabilityRegistry.yaml",
)


class RegistryBundle:
    """In-memory snapshot of all Model Factory registries."""

    def __init__(
        self,
        *,
        providers: Dict[str, Any],
        models: Dict[str, Any],
        profiles: Dict[str, Any],
        capabilities: Dict[str, Any],
        registries_dir: Path,
        family_defaults: Optional[Dict[str, Any]] = None,
        vocabulary: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.providers = providers
        self.models = models
        self.profiles = profiles
        self.capabilities = capabilities
        self.registries_dir = registries_dir
        self.family_defaults = family_defaults or {}
        self.vocabulary = vocabulary or {}


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise RegistryError(f"Registry file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise RegistryError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RegistryError(f"Registry root must be a mapping: {path}")
    return data


def _validate_bundle(
    *,
    models: Dict[str, Any],
    profiles: Dict[str, Any],
    capabilities: Dict[str, Any],
    vocabulary: Dict[str, Any],
) -> None:
    """Fail closed on missing profile models / unknown capability ids."""
    for profile_id, profile in profiles.items():
        if not isinstance(profile, dict):
            raise RegistryError(f"Profile '{profile_id}' must be a mapping")
        default_model = profile.get("default_model") or profile.get("primary")
        if not isinstance(default_model, str) or not default_model.strip():
            raise RegistryError(
                f"Profile '{profile_id}' missing string default_model/primary"
            )
        if default_model not in models:
            raise RegistryError(
                f"Profile '{profile_id}' default_model '{default_model}' "
                f"not in ModelRegistry"
            )
        for key in ("fallback_model",):
            fb = profile.get(key)
            if isinstance(fb, str) and fb and fb not in models:
                raise RegistryError(
                    f"Profile '{profile_id}' {key} '{fb}' not in ModelRegistry"
                )
        fallbacks = profile.get("fallbacks")
        if isinstance(fallbacks, list):
            for fb in fallbacks:
                if isinstance(fb, str) and fb and fb not in models:
                    raise RegistryError(
                        f"Profile '{profile_id}' fallback '{fb}' not in ModelRegistry"
                    )

        requires = profile.get("requires")
        if isinstance(requires, list) and vocabulary:
            for cap_id in requires:
                if cap_id not in vocabulary:
                    raise RegistryError(
                        f"Profile '{profile_id}' requires unknown capability '{cap_id}'"
                    )

    # Opus-5 must stay deleted
    for banned in ("system.ai.claude-opus-5", "claude-opus-5"):
        if banned in models:
            raise RegistryError(f"Banned model still registered: {banned}")


def load_registries(registries_dir: Optional[Path | str] = None) -> RegistryBundle:
    """Load Provider / Model / Profile / Capability registries from disk."""
    root = Path(registries_dir) if registries_dir else _DEFAULT_REGISTRIES_DIR
    if not root.is_dir():
        raise RegistryError(f"Registries directory not found: {root}")

    for name in _REQUIRED_FILES:
        if not (root / name).is_file():
            raise RegistryError(f"Missing required registry: {root / name}")

    provider_doc = _load_yaml(root / "ProviderRegistry.yaml")
    model_doc = _load_yaml(root / "ModelRegistry.yaml")
    profile_doc = _load_yaml(root / "ProfileRegistry.yaml")
    capability_doc = _load_yaml(root / "CapabilityRegistry.yaml")

    providers = provider_doc.get("providers")
    models = model_doc.get("models")
    profiles = profile_doc.get("profiles")
    capabilities = capability_doc.get("capabilities")
    family_defaults = capability_doc.get("family_defaults") or {}
    vocabulary = capability_doc.get("vocabulary") or {}

    if not isinstance(providers, dict) or not providers:
        raise RegistryError("ProviderRegistry.providers must be a non-empty mapping")
    if not isinstance(models, dict) or not models:
        raise RegistryError("ModelRegistry.models must be a non-empty mapping")
    if not isinstance(profiles, dict) or not profiles:
        raise RegistryError("ProfileRegistry.profiles must be a non-empty mapping")
    if not isinstance(capabilities, dict):
        raise RegistryError("CapabilityRegistry.capabilities must be a mapping")
    if not isinstance(family_defaults, dict):
        family_defaults = {}
    if not isinstance(vocabulary, dict):
        vocabulary = {}

    _validate_bundle(
        models=models,
        profiles=profiles,
        capabilities=capabilities,
        vocabulary=vocabulary,
    )

    return RegistryBundle(
        providers=providers,
        models=models,
        profiles=profiles,
        capabilities=capabilities,
        registries_dir=root.resolve(),
        family_defaults=family_defaults,
        vocabulary=vocabulary,
    )

